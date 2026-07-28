import argparse
from app.backend.license import generate_license_key, get_machine_hwid

def main():
    parser = argparse.ArgumentParser(description="Clinic SaaS License Key Generator (For Vendor / Developer)")
    parser.add_argument("--hwid", type=str, help="Client's Hardware ID (e.g. BF51-5B25-C5BB-4599)")
    parser.add_argument("--clinic", type=str, default="Clinique El Rahma", help="Client's Clinic Name (e.g. 'Clinique El Rahma')")
    parser.add_argument("--tier", type=str, default="Premium", choices=["Standard", "Premium"], help="License tier")
    parser.add_argument("--admin", action="store_true", help="Generate Master Admin Key for yourself")
    parser.add_argument("--trial", action="store_true", help="Generate 30-Minute Free Demo Trial Key")
    parser.add_argument("--current", action="store_true", help="Generate key for local machine HWID")

    args = parser.parse_args()

    if args.current:
        target_hwid = get_machine_hwid()
    elif args.hwid:
        target_hwid = args.hwid
    else:
        print("Error: Please provide --hwid <HWID> or use --current to generate for this machine.")
        print("\nUsage Examples:")
        print("  python generate_license.py --hwid BF51-5B25-C5BB-4599 --clinic \"Clinique El Rahma\"")
        print("  python generate_license.py --hwid BF51-5B25-C5BB-4599 --trial")
        print("  python generate_license.py --hwid BF51-5B25-C5BB-4599 --admin")
        return

    if args.trial:
        key = generate_license_key(target_hwid, clinic_name="Clinique Démo", trial=True)
        license_type = "30-MINUTE FREE DEMO TRIAL KEY (Auto-locks after 30 minutes)"
    elif args.admin:
        key = generate_license_key(target_hwid, clinic_name="", tier="Admin", is_admin=True)
        license_type = "MASTER ADMIN KEY (Full Vendor Access & Admin Control Panel)"
    else:
        key = generate_license_key(target_hwid, clinic_name=args.clinic, tier=args.tier, is_admin=False)
        license_type = f"{args.tier.upper()} LICENSE ({args.clinic})"

    print("\n==================================================")
    print("   [+] CLINIC SAAS LICENSE KEY GENERATED")
    print("==================================================")
    print(f"Target Hardware ID (HWID) : {target_hwid}")
    print(f"License Type               : {license_type}")
    if not args.admin and not args.trial:
        print(f"Bound Clinic Name          : {args.clinic}")
    print(f"\nLICENSE KEY ->  {key}")
    print("==================================================")
    print("Send this key to your client. When entered, it unlocks their software!\n")

if __name__ == '__main__':
    main()
