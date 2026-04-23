import requests
from scapy.all import sniff, IP, TCP
API_URL = "http://127.0.0.1:8000/predict"
display_volume = 0
inspection_count = 0
print("🕵️ ASIM ELITE SNIFFER STARTING...")
print("Press Ctrl+C to stop.\n")
def packet_callback(packet):
    global display_volume, inspection_count
    if packet.haslayer(IP) and packet.haslayer(TCP):
        display_volume += len(packet) 
        inspection_count += 1
        payload = {
            "Destination_Port": int(packet[TCP].dport),
            "Total_Fwd_Packets": 2, 
            "Init_Win_bytes_forward": int(packet[TCP].window),
            "Flow_Duration": 1000,
            "custom_total_volume": int(display_volume),
            "custom_event_count": int(inspection_count)
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=0.5)
            if response.status_code == 200:
                res = response.json()
                status = res.get('status', 'NORMAL')
                conf = res.get('rf_confidence', 0)
                port = packet[TCP].dport
                color = "\033[92m" if status == "NORMAL" else "\033[91m"
                print(f"{color}[{status}] Conf: {conf}% | Volume: {display_volume} | Port: {port}\033[0m")
        except Exception:
            pass
try:
    sniff(prn=packet_callback, store=0)
except KeyboardInterrupt:
    print("\n🛑 Sniffer Stopped. Total Volume Processed:", display_volume)