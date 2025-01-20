import os
import subprocess

def generate_view_spectrals(folder_path, folder_name):
    output_base_path = os.path.join(r"\\serverchad\E\RED\Spectrals", folder_name)
    os.makedirs(output_base_path, exist_ok=True)

    for root, _, files in os.walk(folder_path):
        for file in files:
            if not file.endswith(('.flac', '.mp3', '.wav')):
                print(f"\033[93mSkipping unsupported file format: {file}\033[0m")
                continue

            file_path = os.path.join(root, file)
            base_name, _ = os.path.splitext(file)
            full_spectral_path = os.path.join(output_base_path, f"{base_name} - (Full Spec).png")
            partial_spectral_path = os.path.join(output_base_path, f"{base_name} - (Partial Spec).png")

            # Generate full spectral
            subprocess.run(
                [
                    "sox", file_path, "-n", "remix", "1", "spectrogram",
                    "-x", "3000", "-y", "513", "-z", "120", "-w", "Kaiser",
                    "-o", full_spectral_path
                ],
                check=True
            )

            # Generate partial spectral (zoomed-in slice)
            subprocess.run(
                [
                    "sox", file_path, "-n", "remix", "1", "spectrogram",
                    "-X", "200", "-y", "1025", "-z", "120", "-w", "Kaiser",
                    "-S", "1:00", "-d", "0:02",
                    "-o", partial_spectral_path
                ],
                check=True
            )

            # Open the partial spectral using Windows default photo viewer
            try:
                os.startfile(partial_spectral_path)
            except Exception as e:
                print(f"Error opening {partial_spectral_path} in default viewer: {e}")

    print("\033[92mAll spectrals generated and saved successfully.\033[0m")


def spectrals_ok():
    ans = input("Are spectrals ok? (Y/N): ").strip().lower()

    while True:
        if ans in ("y", "yes"):
            return True
        elif ans in ("n", "no"):
            return False
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")
            ans = input("Are spectrals ok? (Y/N): ").strip().lower()
