# Contract: Yamaha YNC Protocol Interface (Android Native)

**Protocol**: Yamaha Network Control (YNC) XML over HTTP
**Target Hardware**: Yamaha RX-V673 (Firmware v1.80+)
**Endpoint**: `http://<AVR_HOST>/YamahaRemoteControl/ctrl`
**HTTP Method**: `POST`
**Headers**:
- `Content-Type`: `text/xml; charset=utf-8`
- `User-Agent`: `AV_Receiver/3.1`

---

## 1. Status & Telemetry Commands (Read-Only)

### 1.1 Basic Status Query
```xml
<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>
```
**Expected Response Extracts**:
- Power: `<Power>On</Power>` | `<Power>Standby</Power>`
- Active Input: `<Input_Sel>AV4</Input_Sel>`
- Master Volume: `<Val>-400</Val>` (Value in tenths of dB, e.g. $-400 = -40.0\text{ dB}$)
- Straight Mode: `<Straight>On</Straight>` | `<Straight>Off</Straight>`
- Sound Program: `<Sound_Program>Standard</Sound_Program>`

### 1.2 PEQ Selection Query
```xml
<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1><PEQ><Sel>GetParam</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>
```
**Expected Response**: `<Sel>Manual</Sel>` | `<Sel>Through</Sel>` | `<Sel>Flat</Sel>`

---

## 2. Hardware Control Commands (Single-Parameter Writes)

### 2.1 Volume Adjustment (Debounced 60ms)
```xml
<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>{valTenthsDb}</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>
```
- Constraints: Clamped between $-800$ and $+165$ ($-80.0\text{ dB}$ to $+16.5\text{ dB}$).
- Steps: Multiples of $5$ ($0.5\text{ dB}$ steps).

### 2.2 PEQ Mode Switch (A/B Comparison)
```xml
<YAMAHA_AV cmd="PUT"><System><Speaker_Preout><Pattern_1><PEQ><Sel>{mode}</Sel></PEQ></Pattern_1></Speaker_Preout></System></YAMAHA_AV>
```
- Allowed Values for `{mode}`: `'Manual'`, `'Through'`, `'Flat'`, `'Front'`.

### 2.3 Input Selection
```xml
<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>{input}</Input_Sel></Input></Main_Zone></YAMAHA_AV>
```
- Allowed Values: `'AV4'`, `'V-AUX'`, `'HDMI1'`, `'AUDIO1'`, `'SERVER'`.

---

## 3. Parametric Equalizer Matrix Deployment (Atomic NVRAM Write)

### 3.1 7-Band PEQ Channel Block
Each channel (`Front_L`, `Front_R`) contains exactly 7 bands:
```xml
<YAMAHA_AV cmd="PUT">
  <System>
    <Speaker_Preout>
      <Pattern_1>
        <PEQ>
          <{Channel}>
            <Band_1>
              <Gain>{gainDbFormatted}</Gain>
              <Freq>{freqFormatted}</Freq>
              <Q>{qFormatted}</Q>
            </Band_1>
            <!-- Bands 2 through 7 -->
          </{Channel}>
        </PEQ>
      </Pattern_1>
    </Speaker_Preout>
  </System>
</YAMAHA_AV>
```

### 3.2 Discrete Formatting Invariants
- **Frequency (`<Freq>`)**: Must match discrete string table, e.g., `'99.2 Hz'`, `'1.00 kHz'`, `'2.52 kHz'`.
- **Quality Factor (`<Q>`)**: Must match discrete string table, e.g., `'0.500'`, `'1.260'`, `'3.175'`, `'10.080'`.
- **Gain (`<Gain>`)**: Formatted as `'0.0 dB'`, `'+2.5 dB'`, `'-4.5 dB'` in $0.5\text{ dB}$ increments.
- **Safety Limit**: Boost strictly $\le +3.0\text{ dB}$; $\le 0.0\text{ dB}$ for $f > 500\text{ Hz}$. Cut $\ge -12.0\text{ dB}$.

---

## 4. Disaster Recovery & Rollback Contract
Before deploying any PEQ parameters, the application MUST query the full Pattern_1 block:
```xml
<YAMAHA_AV cmd="GET"><System><Speaker_Preout><Pattern_1>GetParam</Pattern_1></Speaker_Preout></System></YAMAHA_AV>
```
The exact XML response must be cached locally. On session abort or user rollback request, the application performs an atomic PUT restoring the saved `<Pattern_1>` snapshot.
