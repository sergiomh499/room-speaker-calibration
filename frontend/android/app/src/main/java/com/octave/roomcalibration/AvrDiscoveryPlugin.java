package com.octave.roomcalibration;

import android.content.Context;
import android.net.wifi.WifiManager;
import android.util.Log;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@CapacitorPlugin(name = "AvrDiscovery")
public class AvrDiscoveryPlugin extends Plugin {
    private static final String TAG = "AvrDiscovery";
    private final ExecutorService executor = Executors.newFixedThreadPool(4);

    @PluginMethod
    public void discover(PluginCall call) {
        executor.execute(() -> {
            JSArray foundList = new JSArray();
            WifiManager.MulticastLock lock = null;

            try {
                // Adquirir bloqueo multicast para SSDP
                WifiManager wifi = (WifiManager) getContext().getApplicationContext().getSystemService(Context.WIFI_SERVICE);
                if (wifi != null) {
                    lock = wifi.createMulticastLock("octave_ssdp_lock");
                    lock.acquire();
                }

                // 1. Sondeo SSDP M-SEARCH (UPnP/DLNA) en 239.255.255.250:1900
                String mSearch = "M-SEARCH * HTTP/1.1\r\n" +
                        "HOST: 239.255.255.250:1900\r\n" +
                        "MAN: \"ssdp:discover\"\r\n" +
                        "MX: 2\r\n" +
                        "ST: ssdp:all\r\n\r\n";

                DatagramSocket socket = new DatagramSocket();
                socket.setSoTimeout(1500);
                byte[] sendData = mSearch.getBytes();
                DatagramPacket sendPacket = new DatagramPacket(
                        sendData,
                        sendData.length,
                        InetAddress.getByName("239.255.255.250"),
                        1900
                );
                socket.send(sendPacket);

                byte[] recvBuf = new byte[2048];
                long endTime = System.currentTimeMillis() + 2000;

                while (System.currentTimeMillis() < endTime) {
                    try {
                        DatagramPacket recvPacket = new DatagramPacket(recvBuf, recvBuf.length);
                        socket.receive(recvPacket);
                        String response = new String(recvPacket.getData(), 0, recvPacket.getLength());
                        String senderIp = recvPacket.getAddress().getHostAddress();

                        if (response.toLowerCase().contains("yamaha") || response.toLowerCase().contains("rx-v") || response.contains("MediaRenderer")) {
                            JSObject dev = verifyYamahaDevice(senderIp);
                            if (dev != null) {
                                foundList.put(dev);
                            }
                        }
                    } catch (Exception ignored) {
                        break;
                    }
                }
                socket.close();

            } catch (Exception e) {
                Log.w(TAG, "Error en escaneo SSDP: " + e.getMessage());
            } finally {
                if (lock != null && lock.isHeld()) {
                    lock.release();
                }
            }

            // 2. Si SSDP no encontró o la red bloquea multicast, probar IPs habituales (192.168.1.43, etc.)
            if (foundList.length() == 0) {
                String[] candidateIps = { "192.168.1.43", "192.168.1.45", "192.168.0.43", "192.168.1.50" };
                for (String ip : candidateIps) {
                    JSObject dev = verifyYamahaDevice(ip);
                    if (dev != null) {
                        foundList.put(dev);
                        break;
                    }
                }
            }

            JSObject result = new JSObject();
            result.put("devices", foundList);
            call.resolve(result);
        });
    }

    private JSObject verifyYamahaDevice(String ip) {
        try {
            URL url = new URL("http://" + ip + "/YamahaRemoteControl/ctrl");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setConnectTimeout(1200);
            conn.setReadTimeout(1200);
            conn.setRequestProperty("Content-Type", "text/xml; charset=utf-8");
            conn.setDoOutput(true);

            String xml = "<YAMAHA_AV cmd=\"GET\"><System><Config>GetParam</Config></System></YAMAHA_AV>";
            conn.getOutputStream().write(xml.getBytes("UTF-8"));

            if (conn.getResponseCode() == 200) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line);
                }
                String resp = sb.toString();

                JSObject dev = new JSObject();
                dev.put("ip", ip);
                dev.put("model", extractTag(resp, "Model_Name", "Yamaha AV Receiver"));
                dev.put("version", extractTag(resp, "Version", "1.0"));
                return dev;
            }
        } catch (Exception ignored) {}
        return null;
    }

    private String extractTag(String xml, String tag, String defaultVal) {
        try {
            int start = xml.indexOf("<" + tag + ">");
            int end = xml.indexOf("</" + tag + ">");
            if (start != -1 && end != -1) {
                return xml.substring(start + tag.length() + 2, end);
            }
        } catch (Exception ignored) {}
        return defaultVal;
    }
}
