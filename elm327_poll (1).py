import serial
import time
import csv


PORT = 'COM6'
BAUD = 38400
LOG_FILE = 'coolant_log.csv'

# Known working/supported PIDs for GM2 (you can reduce or expand as needed)
pids = {
    '0105': 'Coolant',
    '010C': 'RPM',
    '0111': 'TPS',
    '010F': 'Intake Temp',
    # '0146': 'Ambient',   # REMOVE: GM2 doesn't support
    # '015C': 'OilTemp',   # REMOVE: GM2 doesn't support
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
        elif pid == '0111' and response.startswith('4111'):
            return round(int(response[4:6], 16) * 100 / 255, 1)
        elif pid == '010F' and response.startswith('410F'):
            return int(response[4:6], 16) - 40
    except Exception as e:
        print(f"[Decode error for {pid}]: {e}")
    return None

def send_and_wait(ser, command, delay=0.3):
    ser.write((command + '\r').encode())
    time.sleep(delay)
    raw = ser.read(200).decode(errors='ignore')
    return raw

def clean_response(raw):
    lines = raw.splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith('>')]

def main():
    print(f"Connecting to {PORT}...")
    with serial.Serial(PORT, BAUD, timeout=1) as ser, open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(list(pids.values()))

        # Init ELM327
        init_cmds = ['ATZ', 'ATE0', 'ATL0', 'ATS0', 'ATH0']
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

                if value is not None:
                    row.append(value)
                else:
                    print(f"[WARN] {pid} response: {raw.strip()}")
                    row.append("NULL")

            print(" | ".join(str(x) for x in row))
            writer.writerow(row)
            f.flush()

            time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
