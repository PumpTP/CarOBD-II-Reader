import serial
import time
import csv

PORT = 'COM7'
BAUD = 38400
LOG_FILE = 'obd_log.csv'

pids = {
    '0105': 'Coolant_Temperature',
    '010C': 'Engine_RPM',
    '010D': 'Vehicle_Speed',
    '0111': 'Throttle_Position',
    '0104': 'Engine_Load',
    '010F': 'Intake_Air_Temp',
    '0110': 'MAF_Air_Flow',
    '0133': 'Absolute_Throttle_Position_B',
    '0149': 'Pedal_Position_D',
    '014A': 'Pedal_Position_E',
    '014C': 'Commanded_Throttle_Actuator',
    '0144': 'Commanded_Equiv_Ratio',
    '0145': 'Relative_Throttle_Position',
    '010E': 'Timing_Advance',
    '0142': 'Control_Module_Voltage',
    '010B': 'Intake_Manifold_Pressure',
    '011F': 'Engine_Run_Time'
}

def decode_pid(pid, response):
    response = response.strip().replace(" ", "")
    try:
        if pid == '0105' and response.startswith('4105'):
            return int(response[4:6], 16) - 40

        elif pid == '010C' and response.startswith('410C'):
            A = int(response[4:6], 16)
            B = int(response[6:8], 16)
            return (A * 256 + B) // 4

        elif pid == '010D' and response.startswith('410D'):
            return int(response[4:6], 16)

        elif pid == '0111' and response.startswith('4111'):
            return round(int(response[4:6], 16) * 100 / 255, 1)

        elif pid == '0104' and response.startswith('4104'):
            return round(int(response[4:6], 16) * 100 / 255, 1)

        elif pid == '010F' and response.startswith('410F'):
            return int(response[4:6], 16) - 40

        elif pid == '0110' and response.startswith('4110'):
            A = int(response[4:6], 16)
            B = int(response[6:8], 16)
            return round((A * 256 + B) / 100.0, 2)


        elif pid == '0133' and response.startswith('4133'):
            return round(int(response[4:6], 16) * 100 / 255, 1)

        elif pid == '0149' and response.startswith('4149'):
            return round(int(response[4:6], 16) * 100 / 255, 1)

        elif pid == '014A' and response.startswith('414A'):
            return round(int(response[4:6], 16) * 100 / 255, 1)

        elif pid == '014C' and response.startswith('414C'):
            return round(int(response[4:6], 16) * 100 / 255, 1)

        elif pid == '0144' and response.startswith('4144'):
            A = int(response[4:6], 16)
            B = int(response[6:8], 16)
            return round((A * 256 + B) / 32768.0, 3)

        elif pid == '0145' and response.startswith('4145'):
            return round(int(response[4:6], 16) * 100 / 255, 1)

        elif pid == '010E' and response.startswith('410E'):
            return round((int(response[4:6], 16) / 2) - 64, 1)


        elif pid == '0142' and response.startswith('4142'):
            A = int(response[4:6], 16)
            B = int(response[6:8], 16)
            return round((A * 256 + B) / 1000.0, 2)

        elif pid == '010B' and response.startswith('410B'):
            return int(response[4:6], 16)  # kPa


        elif pid == '011F' and response.startswith('411F'):
            A = int(response[4:6], 16)
            B = int(response[6:8], 16)
            return A * 256 + B  # seconds

    except Exception as e:
        print(f"[Decode error for {pid}]: {e}")
    return None

def send_and_wait(ser, command, delay=0.3):
    ser.write((command + '\r').encode())
    time.sleep(delay)
    raw = ser.read(200).decode(errors='ignore')
    print(f">>> {command}\n{raw.strip()}")
    return raw

def clean_response(raw):
    lines = raw.splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith('>')]

def main():
    print(f"Connecting to {PORT}...")
    with serial.Serial(PORT, BAUD, timeout=1) as ser, open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(list(pids.values()))

        init_cmds = ['ATZ', 'ATE0', 'ATL0', 'ATS0', 'ATH0', 'ATSP0', 'ATDP']
        for cmd in init_cmds:
            print(f"Init: {cmd}")
            send_and_wait(ser, cmd, 0.5)
        print("\nPolling...\nPress Ctrl+C to stop.\n")

        while True:
            row = []
            for pid in pids:
                raw = send_and_wait(ser, pid, 0.3)
                cleaned = clean_response(raw)

                value = None
                for line in cleaned:
                    if line.startswith('41'):
                        value = decode_pid(pid, line)
                        break

                row.append(value if value is not None else "NULL")

            print(" | ".join(str(x) for x in row))
            writer.writerow(row)
            f.flush()
            # time.sleep(0.5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
