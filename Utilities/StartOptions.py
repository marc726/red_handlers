    
def start_options():

    options = input("Transcode to MP3V0 and MP3320? (Y/N): ").strip().lower()

    while True:
        if options == "y" or options == "yes":
            print("Transcoding enabled!")
            return True
        elif options == "n" or options == "no":
            print("Transcoding disabled!")  
            return False
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")
            options = input("Transcode to MP3V0 and MP3320? (Y/N): ").strip().lower()
