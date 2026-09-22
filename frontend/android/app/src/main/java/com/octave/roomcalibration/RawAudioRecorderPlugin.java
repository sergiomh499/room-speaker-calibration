package com.octave.roomcalibration;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.media.AudioDeviceInfo;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Build;
import android.util.Log;

import androidx.core.app.ActivityCompat;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;

import java.io.File;
import java.io.FileOutputStream;
import java.io.RandomAccessFile;
import java.util.concurrent.atomic.AtomicBoolean;

@CapacitorPlugin(
    name = "RawAudioRecorder",
    permissions = {
        @Permission(
            alias = "audio",
            strings = { Manifest.permission.RECORD_AUDIO }
        )
    }
)
public class RawAudioRecorderPlugin extends Plugin {
    private static final String TAG = "RawAudioRecorder";
    private static final int SAMPLE_RATE = 48000;
    private static final int CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO;
    private static final int AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT;

    private AudioRecord audioRecord = null;
    private Thread recordingThread = null;
    private final AtomicBoolean isRecording = new AtomicBoolean(false);
    private File currentWavFile = null;
    private long recordingStartTime = 0;

    @PluginMethod
    public void getAudioDevices(PluginCall call) {
        JSObject result = new JSObject();
        JSArray devicesArray = new JSArray();

        AudioManager audioManager = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);
        if (audioManager != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            AudioDeviceInfo[] devices = audioManager.getDevices(AudioManager.GET_DEVICES_INPUTS);
            for (AudioDeviceInfo dev : devices) {
                JSObject devObj = new JSObject();
                devObj.put("id", dev.getId());
                devObj.put("name", dev.getProductName().toString());
                int type = dev.getType();
                boolean isUsb = (type == AudioDeviceInfo.TYPE_USB_DEVICE || type == AudioDeviceInfo.TYPE_USB_HEADSET);
                devObj.put("isUsb", isUsb);
                devObj.put("type", typeToString(type));
                devicesArray.put(devObj);
            }
        }
        result.put("devices", devicesArray);
        result.put("sampleRate", SAMPLE_RATE);
        result.put("unprocessedSupported", Build.VERSION.SDK_INT >= Build.VERSION_CODES.N);
        call.resolve(result);
    }

    @PluginMethod
    public void startRecording(PluginCall call) {
        if (!getPermissionState("audio").equals(com.getcapacitor.PermissionState.GRANTED)) {
            requestPermissionForAlias("audio", call, "audioPermCallback");
            return;
        }

        if (isRecording.get()) {
            call.reject("Ya hay una grabación acústica en curso");
            return;
        }

        String filename = call.getString("filename", "acoustic_sweep_" + System.currentTimeMillis() + ".wav");
        File dir = getContext().getCacheDir();
        currentWavFile = new File(dir, filename);

        int bufferSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT);
        if (bufferSize < 0) {
            bufferSize = SAMPLE_RATE * 2;
        }

        // Selección de fuente cruda profesional (UNPROCESSED evita filtros paso-alto y AGC de Android)
        int audioSource = MediaRecorder.AudioSource.MIC;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            audioSource = MediaRecorder.AudioSource.UNPROCESSED;
        } else {
            audioSource = MediaRecorder.AudioSource.VOICE_RECOGNITION;
        }

        try {
            if (ActivityCompat.checkSelfPermission(getContext(), Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                call.reject("Permiso RECORD_AUDIO no concedido");
                return;
            }

            audioRecord = new AudioRecord(audioSource, SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT, bufferSize * 2);

            // Si hay un micrófono USB conectado (ej. miniDSP UMIK-1 / UMM-6), darle preferencia automática
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                AudioManager audioManager = (AudioManager) getContext().getSystemService(Context.AUDIO_SERVICE);
                if (audioManager != null) {
                    AudioDeviceInfo[] devices = audioManager.getDevices(AudioManager.GET_DEVICES_INPUTS);
                    for (AudioDeviceInfo dev : devices) {
                        if (dev.getType() == AudioDeviceInfo.TYPE_USB_DEVICE || dev.getType() == AudioDeviceInfo.TYPE_USB_HEADSET) {
                            audioRecord.setPreferredDevice(dev);
                            Log.i(TAG, "Micrófono USB preferido asignado: " + dev.getProductName());
                            break;
                        }
                    }
                }
            }

            if (audioRecord.getState() != AudioRecord.STATE_INITIALIZED) {
                // Fallback a fuente MIC estándar si el hardware no soporta UNPROCESSED
                audioRecord = new AudioRecord(MediaRecorder.AudioSource.MIC, SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT, bufferSize * 2);
            }

            audioRecord.startRecording();
            isRecording.set(true);
            recordingStartTime = System.currentTimeMillis();

            final int finalBufferSize = bufferSize;
            recordingThread = new Thread(() -> writeAudioDataToWav(currentWavFile, finalBufferSize), "AcousticRecordThread");
            recordingThread.start();

            JSObject res = new JSObject();
            res.put("recording", true);
            res.put("filePath", currentWavFile.getAbsolutePath());
            res.put("audioSource", audioSource == MediaRecorder.AudioSource.UNPROCESSED ? "UNPROCESSED_RAW" : "STANDARD_MIC");
            res.put("sampleRate", SAMPLE_RATE);
            call.resolve(res);

        } catch (Exception e) {
            Log.e(TAG, "Error iniciando grabación acústica: " + e.getMessage());
            call.reject("Fallo al iniciar AudioRecord: " + e.getMessage());
        }
    }

    @PluginMethod
    public void stopRecording(PluginCall call) {
        if (!isRecording.get()) {
            call.reject("No hay grabación activa");
            return;
        }

        isRecording.set(false);

        try {
            if (audioRecord != null) {
                audioRecord.stop();
                audioRecord.release();
                audioRecord = null;
            }

            if (recordingThread != null) {
                recordingThread.join(2000);
                recordingThread = null;
            }

            long durationMs = System.currentTimeMillis() - recordingStartTime;

            // Finalizar cabecera RIFF del archivo WAV
            updateWavHeader(currentWavFile);

            JSObject res = new JSObject();
            res.put("success", true);
            res.put("filePath", currentWavFile.getAbsolutePath());
            res.put("fileName", currentWavFile.getName());
            res.put("durationMs", durationMs);
            res.put("fileSizeBytes", currentWavFile.length());
            call.resolve(res);

        } catch (Exception e) {
            Log.e(TAG, "Error deteniendo grabación: " + e.getMessage());
            call.reject("Error finalizando archivo WAV: " + e.getMessage());
        }
    }

    @PluginMethod
    public void getRecordingStatus(PluginCall call) {
        JSObject res = new JSObject();
        res.put("isRecording", isRecording.get());
        res.put("elapsedMs", isRecording.get() ? (System.currentTimeMillis() - recordingStartTime) : 0);
        call.resolve(res);
    }

    private void writeAudioDataToWav(File wavFile, int bufferSize) {
        byte[] data = new byte[bufferSize];
        FileOutputStream fos = null;

        try {
            fos = new FileOutputStream(wavFile);
            // Escribir cabecera provisional de 44 bytes
            byte[] header = new byte[44];
            fos.write(header);

            while (isRecording.get()) {
                int read = audioRecord.read(data, 0, bufferSize);
                if (read > 0) {
                    fos.write(data, 0, read);
                }
            }
            fos.flush();
        } catch (Exception e) {
            Log.e(TAG, "Error en bucle de escritura PCM: " + e.getMessage());
        } finally {
            if (fos != null) {
                try {
                    fos.close();
                } catch (Exception ignored) {}
            }
        }
    }

    private void updateWavHeader(File wavFile) {
        try (RandomAccessFile raf = new RandomAccessFile(wavFile, "rw")) {
            long totalAudioLen = wavFile.length() - 44;
            long totalDataLen = totalAudioLen + 36;
            int channels = 1;
            long byteRate = SAMPLE_RATE * channels * 2;

            byte[] header = new byte[44];
            // RIFF/WAVE
            header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
            header[4] = (byte) (totalDataLen & 0xff);
            header[5] = (byte) ((totalDataLen >> 8) & 0xff);
            header[6] = (byte) ((totalDataLen >> 16) & 0xff);
            header[7] = (byte) ((totalDataLen >> 24) & 0xff);
            header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
            // fmt
            header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
            header[16] = 16; header[17] = 0; header[18] = 0; header[19] = 0; // Sub-chunk 1 size (16 for PCM)
            header[20] = 1; header[21] = 0; // AudioFormat (1 = PCM)
            header[22] = (byte) channels; header[23] = 0;
            header[24] = (byte) (SAMPLE_RATE & 0xff);
            header[25] = (byte) ((SAMPLE_RATE >> 8) & 0xff);
            header[26] = (byte) ((SAMPLE_RATE >> 16) & 0xff);
            header[27] = (byte) ((SAMPLE_RATE >> 24) & 0xff);
            header[28] = (byte) (byteRate & 0xff);
            header[29] = (byte) ((byteRate >> 8) & 0xff);
            header[30] = (byte) ((byteRate >> 16) & 0xff);
            header[31] = (byte) ((byteRate >> 24) & 0xff);
            header[32] = (byte) (channels * 2); header[33] = 0; // Block align
            header[34] = 16; header[35] = 0; // Bits per sample
            // data
            header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
            header[40] = (byte) (totalAudioLen & 0xff);
            header[41] = (byte) ((totalAudioLen >> 8) & 0xff);
            header[42] = (byte) ((totalAudioLen >> 16) & 0xff);
            header[43] = (byte) ((totalAudioLen >> 24) & 0xff);

            raf.seek(0);
            raf.write(header);
        } catch (Exception e) {
            Log.e(TAG, "Error finalizando cabecera WAV: " + e.getMessage());
        }
    }

    private String typeToString(int type) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            switch (type) {
                case AudioDeviceInfo.TYPE_BUILTIN_MIC: return "Micrófono Integrado Teléfono";
                case AudioDeviceInfo.TYPE_USB_DEVICE: return "Micrófono Calibrado USB (UMIK-1/UMM-6)";
                case AudioDeviceInfo.TYPE_USB_HEADSET: return "Dispositivo Audio USB-C";
                case AudioDeviceInfo.TYPE_WIRED_HEADSET: return "Auricular con Micrófono";
                case AudioDeviceInfo.TYPE_BLUETOOTH_SCO: return "Bluetooth SCO";
                default: return "Audio Input (" + type + ")";
            }
        }
        return "Audio Input";
    }
}
