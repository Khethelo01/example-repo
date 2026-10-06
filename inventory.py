import csv
import math
from pathlib import Path


# Find inventory.txt in the same folder as this Python file.
INVENTORY_FILE = Path(__file__).with_name("inventory.txt")


class Shoe:
    """Represent one shoe product in the warehouse."""

    def __init__(self, country, code, product, cost, quantity):
        # Store the information belonging to this shoe object.
        self.country = country
        self.code = code
        self.product = product
        self.cost = cost
        self.quantity = quantity

    def get_cost(self):
        """Return the cost of one pair of shoes."""
        return self.cost

    def get_quantity(self):
        """Return the number of pairs in stock."""
        return self.quantity

    def __str__(self):
        """Return labelled shoe details for readable output."""
        return (
            f"Country:  {self.country}\n"
            f"Code:     {self.code}\n"
            f"Product:  {self.product}\n"
            f"Cost:     {self.cost:.2f}\n"
            f"Quantity: {self.quantity}"
        )


# Store all Shoe objects outside the class, as required.
shoes_list = []


def read_shoes_data():
    """Read the inventory file and create Shoe objects."""
    loaded_shoes = []
    seen_codes = set()

    try:
        with INVENTORY_FILE.open(
            "r", encoding="utf-8-sig", newline=""
        ) as inventory_file:
            reader = csv.reader(inventory_file)

            # Skip the first line because it contains column headings.
            next(reader, None)

            for line_number, row in enumerate(reader, start=2):
                # Ignore completely empty lines.
                if not row:
                    continue

                if len(row) != 5:
                    raise ValueError(
                        f"Line {line_number} must contain five fields."
                    )

                country, code, product, cost, quantity = (
                    field.strip() for field in row
                )

                if not country or not code or not product:
                    raise ValueError(
                        f"Line {line_number} contains an empty field."
                    )

                # Convert numbers before using them in calculations.
                cost = float(cost)
                quantity = int(quantity)

                if not math.isfinite(cost) or cost < 0 or quantity < 0:
                    raise ValueError(
                        f"Line {line_number} contains an invalid number."
                    )

                # Product codes must be unique, regardless of case.
                if code.casefold() in seen_codes:
                    raise ValueError(
                        f"Line {line_number} contains a duplicate code."
                    )

                seen_codes.add(code.casefold())
                loaded_shoes.append(
                    Shoe(country, code, product, cost, quantity)
                )

    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        print(f"Could not load inventory: {error}")
        return False

    # Only replace the list after the entire file loads successfully.
    # This also prevents duplicates if the function is called again.
    shoes_list.clear()
    shoes_list.extend(loaded_shoes)
    return True


def save_shoes_data():
    """Save the current inventory, including changed quantities."""
    # Write a temporary file first to protect the original inventory
    # if writing fails before the new file is complete.
    temporary_file = INVENTORY_FILE.with_suffix(".tmp")

    try:
        with temporary_file.open(
            "w", encoding="utf-8", newline=""
        ) as inventory_file:
            writer = csv.writer(inventory_file)
            writer.writerow(
                ["Country", "Code", "Product", "Cost", "Quantity"]
            )

            for shoe in shoes_list:
                writer.writerow(
                    [
                        shoe.country,
                        shoe.code,
                        shoe.product,
                        shoe.cost,
                        shoe.quantity,
                    ]
                )

        temporary_file.replace(INVENTORY_FILE)
        return True

    except OSError as error:
        print(f"Could not save inventory: {error}")
        return False


def get_text(prompt):
    """Keep asking until the user enters non-empty text."""
    while True:
        text = input(prompt).strip()

        if text:
            return text

        print("This field cannot be empty.")


def get_number(prompt, whole_number=False, minimum=0):
    """Validate a number and return it as an integer or float."""
    while True:
        try:
            user_input = input(prompt).strip()

            if whole_number:
                number = int(user_input)
            else:
                number = float(user_input)

            # Reject negative values and special values such as NaN.
            if (
                not whole_number and not math.isfinite(number)
            ) or number < minimum:
                raise ValueError

            return number

        except ValueError:
            number_type = "whole number" if whole_number else "number"
            print(
                f"Enter a valid {number_type} of at least {minimum}."
            )


def capture_shoes():
    """Capture a new shoe and add it to the inventory."""
    country = get_text("Country: ")

    while True:
        code = get_text("Shoe code: ")

        # Prevent two products from sharing the same code.
        if any(
            shoe.code.casefold() == code.casefold()
            for shoe in shoes_list
        ):
            print("That code already exists. Enter a different code.")
        else:
            break

    product = get_text("Product name: ")
    cost = get_number("Cost per pair: ")
    quantity = get_number("Quantity: ", whole_number=True)

    new_shoe = Shoe(country, code, product, cost, quantity)
    shoes_list.append(new_shoe)

    if save_shoes_data():
        print("New shoe added and saved.")
    else:
        # Undo the change if it could not be saved.
        shoes_list.pop()
        print("The new shoe was not added.")


def view_all():
    """Print every shoe using its __str__ method."""
    if not shoes_list:
        print("There are no shoes in the inventory.")
        return

    for shoe in shoes_list:
        print("-" * 40)
        print(shoe)

    print("-" * 40)


def re_stock():
    """Find the lowest quantity and offer to increase it."""
    if not shoes_list:
        print("There are no shoes to restock.")
        return

    # min() selects the object with the smallest quantity.
    lowest_shoe = min(
        shoes_list, key=lambda shoe: shoe.get_quantity()
    )

    print("\nShoe with the lowest quantity:")
    print(lowest_shoe)

    while True:
        answer = input("Restock this shoe? (yes/no): ").strip().lower()

        if answer in ("yes", "y", "no", "n"):
            break

        print("Please enter yes or no.")

    if answer in ("no", "n"):
        print("Restocking cancelled.")
        return

    additional_quantity = get_number(
        "How many pairs should be added? ",
        whole_number=True,
        minimum=1,
    )

    previous_quantity = lowest_shoe.quantity
    lowest_shoe.quantity += additional_quantity

    # Save the updated quantity to inventory.txt.
    if save_shoes_data():
        print(f"New quantity: {lowest_shoe.quantity}")
    else:
        lowest_shoe.quantity = previous_quantity
        print("The quantity was not changed.")


def search_shoe():
    """Search by code and return the matching Shoe object."""
    code = get_text("Enter the shoe code to search for: ")

    for shoe in shoes_list:
        if shoe.code.casefold() == code.casefold():
            return shoe

    # None tells the menu that no matching object was found.
    return None


def value_per_item():
    """Calculate the stock value of each shoe product."""
    if not shoes_list:
        print("There are no shoes in the inventory.")
        return

    for shoe in shoes_list:
        # Stock value equals unit cost multiplied by quantity.
        value = shoe.get_cost() * shoe.get_quantity()
        print(f"{shoe.code} | {shoe.product} | Value: {value:.2f}")


def highest_qty():
    """Display the shoe product with the highest quantity."""
    if not shoes_list:
        print("There are no shoes in the inventory.")
        return

    highest_shoe = max(
        shoes_list, key=lambda shoe: shoe.get_quantity()
    )

    print("\nShoe with the highest quantity:")
    print(highest_shoe)


def main():
    """Load the inventory and run the menu."""
    if not read_shoes_data():
        # Stop if loading fails so existing data is not overwritten.
        return

    while True:
        print(
            "\nSHOE INVENTORY MENU\n"
            "1. View all shoes\n"
            "2. Capture a new shoe\n"
            "3. Restock the lowest quantity\n"
            "4. Search for a shoe\n"
            "5. View value per item\n"
            "6. View highest quantity\n"
            "0. Exit"
        )

        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_all()
        elif choice == "2":
            capture_shoes()
        elif choice == "3":
            re_stock()
        elif choice == "4":
            shoe = search_shoe()

            if shoe is None:
                print("No shoe was found with that code.")
            else:
                print(shoe)
        elif choice == "5":
            value_per_item()
        elif choice == "6":
            highest_qty()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Choose a number from the menu.")


# Run the menu only when this file is executed directly.
if __name__ == "__main__":
    main()