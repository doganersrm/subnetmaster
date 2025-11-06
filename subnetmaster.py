#!/usr/bin/env python3
import ipaddress
import math
import os

def calculate_subnets(ip: str, cidr: int, num_subnets: int):
    # Ağ nesnesini güvenli biçimde oluştur
    try:
        network = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError):
        print("Geçersiz CIDR değeri veya IP adresi! Lütfen geçerli bir IP adresi ve CIDR değeri girin.")
        return [], 0, 0, 0

    if num_subnets <= 0:
        print("Geçersiz subnet sayısı! Subnet sayısı pozitif bir tamsayı olmalıdır.")
        return [], 0, 0, 0

    # İstenen alt ağ sayısını karşılamak için gereken yeni prefix (yukarı yuvarlanır)
    needed_bits = math.ceil(math.log2(num_subnets))
    new_prefix = cidr + needed_bits

    if new_prefix > 32:
        print("İstenen sayıda alt ağa bölmek için yeterli bit yok. Daha büyük bir ağ aralığı seçin veya alt ağ sayısını azaltın.")
        return [], 0, 0, 0

    # Alt ağları üret
    try:
        all_subnets = list(network.subnets(new_prefix=new_prefix))
    except ValueError as e:
        print(f"Alt ağ hesaplaması başarısız: {e}")
        return [], 0, 0, 0

    # İstenen kadarını al (mümkün olandan fazla istenirse sadece mevcut olanlar alınır)
    subnets = all_subnets[:num_subnets]

    subnet_info = []
    total_hosts = 0

    for subnet in subnets:
        network_address = subnet.network_address
        subnet_mask = subnet.netmask

        if subnet.prefixlen < 31:
            first_usable_ip = subnet[1]
            last_usable_ip = subnet[-2]
            subnet_hosts = (2 ** (32 - subnet.prefixlen)) - 2
        else:
            # /31 ve /32 için özel durum: tüm adresler kullanılabilir kabul edilir
            first_usable_ip = subnet[0]
            last_usable_ip = subnet[-1]
            subnet_hosts = (2 ** (32 - subnet.prefixlen))

        broadcast_address = subnet.broadcast_address

        subnet_info.append({
            "Ağ Adresi": str(network_address),
            "Subnet Mask": str(subnet_mask),
            "İlk Kullanılabilir IP": str(first_usable_ip),
            "Son Kullanılabilir IP": str(last_usable_ip),
            "Broadcast Adresi": str(broadcast_address),
            "Kullanılabilir Host Sayısı": subnet_hosts
        })
        total_hosts += subnet_hosts

    # (subnet_info, total_hosts, new_prefix, available_subnet_count)
    return subnet_info, total_hosts, new_prefix, len(all_subnets)

def display_subnet_info(subnet_info, total_hosts, requested_count, new_prefix, available_count):
    actual_count = len(subnet_info)
    print(f"İstenen: {requested_count} alt ağ. Oluşturulan: {actual_count}/{available_count} alt ağ, /{new_prefix} maske ile.")
    print(f"Toplam {total_hosts} kullanılabilir host adresi vardır.\n")

    if not subnet_info:
        return

    max_length = max(len(key) for info in subnet_info for key in info.keys())
    for i, info in enumerate(subnet_info, 1):
        print(f"Subnet {i}:")
        for key, value in info.items():
            padding = ' ' * (max_length - len(key) + 1)
            if key in ("Ağ Adresi", "İlk Kullanılabilir IP", "Son Kullanılabilir IP", "Broadcast Adresi"):
                print(f"{key}:{padding}{value} ({ip_to_binary(value)})")
            elif key == "Subnet Mask":
                print(f"{key}:{padding}{value} ({subnet_mask_to_binary(value)})")
            else:
                print(f"{key}:{padding}{value}")
        print()

def ip_to_binary(ip):
    return '.'.join(f'{int(octet):08b}' for octet in ip.split('.'))

def subnet_mask_to_binary(subnet_mask):
    binary_mask = ''.join(f'{int(octet):08b}' for octet in subnet_mask.split('.'))
    return '.'.join([binary_mask[:8], binary_mask[8:16], binary_mask[16:24], binary_mask[24:]])

def save_to_file(subnet_info, filename="subnet_info.txt"):
    with open(filename, 'w', encoding='utf-8') as file:
        for i, info in enumerate(subnet_info, 1):
            file.write(f"Subnet {i}:\n")
            for key, value in info.items():
                if key in ("Ağ Adresi", "İlk Kullanılabilir IP", "Son Kullanılabilir IP", "Broadcast Adresi"):
                    file.write(f"{key}: {value} ({ip_to_binary(value)})\n")
                elif key == "Subnet Mask":
                    file.write(f"{key}: {value} ({subnet_mask_to_binary(value)})\n")
                else:
                    file.write(f"{key}: {value}\n")
            file.write("\n")

def main():
    print("****************************************************")
    print("*            Subnet Hesaplama Aracı                *")
    print("*                Doğaner Serim                     *")
    print("****************************************************\n")

    while True:
        ip_address = input("IP adresini girin: ").strip()
        try:
            ipaddress.IPv4Address(ip_address)
        except ipaddress.AddressValueError:
            print("Geçersiz IP adresi! Lütfen geçerli bir IPv4 adresi girin.")
            continue

        # CIDR girişi
        try:
            cidr = int(input("CIDR değerini girin (ör. 25): ").strip())
        except ValueError:
            print("Geçersiz giriş! CIDR tamsayı olmalıdır.")
            continue

        if not 0 <= cidr <= 32:
            print("Geçersiz CIDR değeri! CIDR değeri 0 ile 32 arasında olmalıdır.")
            continue

        # Alt ağ sayısı girişi
        try:
            num_subnets = int(input("Kaç alt ağa bölmek istiyorsunuz: ").strip())
        except ValueError:
            print("Geçersiz giriş! Alt ağ sayısı tamsayı olmalıdır.")
            continue

        subnet_info, total_hosts, new_prefix, available_count = calculate_subnets(ip_address, cidr, num_subnets)

        if subnet_info:
            display_subnet_info(subnet_info, total_hosts, num_subnets, new_prefix, available_count)

        # Komut döngüsü
        while True:
            command = input("Komut girin (reset, exit, save): ").strip().lower()
            if command == "reset":
                os.system('cls' if os.name == 'nt' else 'clear')
                break
            elif command == "exit":
                return
            elif command == "save":
                save_to_file(subnet_info)
                print("Bilgiler kaydedildi.")
            else:
                print("Geçersiz komut. Lütfen tekrar deneyin.")

if __name__ == "__main__":
    main()
