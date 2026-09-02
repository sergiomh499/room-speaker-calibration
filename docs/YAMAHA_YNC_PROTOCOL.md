# Protocolo de Control XML Nativo (YNC) - Yamaha RX-V673

Este documento registra la especificación exacta de comandos HTTP/XML (`/YamahaRemoteControl/ctrl`) para la gestión y programación persistente de **Escenas (SCENE 1 a 4)** y control directo del receptor Yamaha RX-V673.

---

## 1. Renombrar Escenas (Almacenamiento Persistente en NVRAM)

> **Regla Crítica**: No utilizar `<Scene_Sel_Item>` (devuelve `RC="3"` / Read-Only). La estructura válida es `<Main_Zone><Scene><Scene_N><Name>`.

### Payload XML para Renombrar las 4 Escenas:
```xml
<YAMAHA_AV cmd="PUT">
  <Main_Zone>
    <Scene>
      <Scene_1><Name>Música Hi-Fi</Name></Scene_1>
      <Scene_2><Name>Cine y Series</Name></Scene_2>
      <Scene_3><Name>TV y Series</Name></Scene_3>
      <Scene_4><Name>Pure Direct</Name></Scene_4>
    </Scene>
  </Main_Zone>
</YAMAHA_AV>
```

---

## 2. Programar Parámetros Persistentes de una Escena

Permite asociar a cada botón de escena la entrada (`AV4`), el estado de `Pure Direct`, `Straight` y el `Sound_Program` (Standard, Drama, etc.):

### Ejemplo: Programar SCENE 3 (TV y Series - Drama DSP):
```xml
<YAMAHA_AV cmd="PUT">
  <Main_Zone>
    <Scene>
      <Scene_3>
        <Input><Input_Sel>AV4</Input_Sel></Input>
        <Sound_Video>
          <Pure_Direct><Mode>Off</Mode></Pure_Direct>
          <HDMI><Output><OUT_1>On</OUT_1></Output></HDMI>
        </Sound_Video>
        <Surround>
          <Program_Sel>
            <Current>
              <Straight>Off</Straight>
              <Enhancer>Off</Enhancer>
              <Sound_Program>Drama</Sound_Program>
            </Current>
          </Program_Sel>
        </Surround>
      </Scene_3>
    </Scene>
  </Main_Zone>
</YAMAHA_AV>
```

### Ejemplo: Programar SCENE 4 (Pure Direct):
```xml
<YAMAHA_AV cmd="PUT">
  <Main_Zone>
    <Scene>
      <Scene_4>
        <Input><Input_Sel>AV4</Input_Sel></Input>
        <Sound_Video>
          <Pure_Direct><Mode>On</Mode></Pure_Direct>
          <HDMI><Output><OUT_1>On</OUT_1></Output></HDMI>
        </Sound_Video>
        <Surround>
          <Program_Sel>
            <Current>
              <Straight>On</Straight>
              <Enhancer>Off</Enhancer>
            </Current>
          </Program_Sel>
        </Surround>
      </Scene_4>
    </Scene>
  </Main_Zone>
</YAMAHA_AV>
```

---

## 3. Consultas de Estado y Verificación

* **Consultar los nombres de todas las escenas**:
  ```xml
  <YAMAHA_AV cmd="GET"><Main_Zone><Config>GetParam</Config></Main_Zone></YAMAHA_AV>
  ```
  *(Devuelve `<Name><Scene><Scene_1>...</Scene_1></Scene></Name>`)*.

* **Consultar la configuración guardada de una escena concreta**:
  ```xml
  <YAMAHA_AV cmd="GET"><Main_Zone><Scene><Scene_3>GetParam</Scene_3></Scene></Main_Zone></YAMAHA_AV>
  ```

* **Activar / Seleccionar una escena**:
  ```xml
  <YAMAHA_AV cmd="PUT"><Main_Zone><Scene><Scene_Sel>Scene 1</Scene_Sel></Scene></Main_Zone></YAMAHA_AV>
  ```

---

## 4. Emulación de Teclas del Mando a Distancia (`Virtual Remote`)

* **Abrir Menú en Pantalla (On Screen)**:
  ```xml
  <YAMAHA_AV cmd="PUT"><Main_Zone><List_Control><Menu_Control>On Screen</Menu_Control></List_Control></Main_Zone></YAMAHA_AV>
  ```
* **Navegación por Cursores (`Up`, `Down`, `Left`, `Right`, `Sel`, `Return`)**:
  ```xml
  <YAMAHA_AV cmd="PUT"><Main_Zone><List_Control><Cursor>Up</Cursor></List_Control></Main_Zone></YAMAHA_AV>
  ```
