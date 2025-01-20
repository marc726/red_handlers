def view_page():
    page = input("What page number would you like to view? (1-25)(Default is 1 if not entered): ").strip()

    while True:
        if page == "":
            return None
        elif page.isnumeric():
            page_number = int(page)
            if 1 <= page_number <= 25:
                return page_number
            else:
                print("Invalid page number. Please enter a number between 1 and 25:")
        
        page = input("What page number would you like to view? (Default is 1 if not entered): ").strip()