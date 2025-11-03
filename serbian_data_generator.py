"""
Serbian data generator for realistic form filling.
Generates random Serbian names, addresses, and phone numbers.
"""
import random


class SerbianDataGenerator:
    """Generate random Serbian personal data."""

    # Common Serbian first names
    MALE_FIRST_NAMES = [
        "Marko", "Nikola", "Stefan", "Luka", "Milan", "Petar", "Nemanja",
        "Aleksandar", "Jovan", "Miloš", "Đorđe", "Filip", "Dušan", "Vladimir",
        "Ivan", "Danilo", "Nenad", "Dejan", "Zoran", "Dragan"
    ]

    FEMALE_FIRST_NAMES = [
        "Ana", "Jelena", "Marija", "Milica", "Jovana", "Ivana", "Katarina",
        "Teodora", "Nina", "Sara", "Maja", "Sanja", "Aleksandra", "Dragana",
        "Tamara", "Nevena", "Sonja", "Vesna", "Nataša", "Jasmina"
    ]

    # Common Serbian last names
    LAST_NAMES = [
        "Jovanović", "Petrović", "Nikolić", "Marković", "Đorđević", "Ilić",
        "Pavlović", "Stanković", "Milošević", "Popović", "Stojanović", "Živković",
        "Dimitrijević", "Todorović", "Mladenović", "Kostić", "Simić", "Radovanović",
        "Stefanović", "Marinković", "Vasić", "Đukić", "Kovačević", "Mitrović"
    ]

    # Serbian cities
    CITIES = [
        "Beograd", "Novi Sad", "Niš", "Kragujevac", "Subotica", "Zrenjanin",
        "Pančevo", "Čačak", "Kruševac", "Smederevo", "Leskovac", "Novi Pazar",
        "Vranje", "Užice", "Valjevo", "Šabac", "Sombor", "Požarevac", "Pirot",
        "Zaječar", "Kikinda", "Sremska Mitrovica", "Vršac", "Jagodina"
    ]

    # Common street names in Serbia
    STREET_NAMES = [
        "Kralja Petra", "Knez Mihailova", "Bulevar Oslobođenja", "Cara Dušana",
        "Nemanjina", "Vojvode Stepe", "Svetog Save", "Vojvode Mišića",
        "Narodnih Heroja", "Partizanska", "Karađorđeva", "Maksima Gorkog",
        "Jug Bogdanova", "Jovana Cvijića", "Bulevar Kralja Aleksandra",
        "Resavska", "Terazije", "Takovska", "Balkanska", "Makedonska"
    ]

    # Phone prefixes (as specified)
    PHONE_PREFIXES = ["063", "064", "069"]

    @staticmethod
    def generate_name(gender=None):
        """
        Generate a random Serbian full name.

        Args:
            gender: 'male', 'female', or None (random)

        Returns:
            str: Full name (first name + last name)
        """
        if gender is None:
            gender = random.choice(['male', 'female'])

        if gender == 'male':
            first_name = random.choice(SerbianDataGenerator.MALE_FIRST_NAMES)
        else:
            first_name = random.choice(SerbianDataGenerator.FEMALE_FIRST_NAMES)

        last_name = random.choice(SerbianDataGenerator.LAST_NAMES)
        return f"{first_name} {last_name}"

    @staticmethod
    def generate_phone():
        """
        Generate a random Serbian phone number starting with 063, 064, or 069.

        Returns:
            str: Phone number in format 06X/XXXXXXX or 06XXXXXXXXX
        """
        prefix = random.choice(SerbianDataGenerator.PHONE_PREFIXES)
        # Generate 6 or 7 remaining digits
        remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        return f"{prefix}{remaining_digits}"

    @staticmethod
    def generate_address():
        """
        Generate a random Serbian address.

        Returns:
            dict: Dictionary with 'street', 'city', and 'postal_code'
        """
        street_name = random.choice(SerbianDataGenerator.STREET_NAMES)
        street_number = random.randint(1, 200)
        city = random.choice(SerbianDataGenerator.CITIES)

        # Generate a realistic postal code (5 digits, typically starts with 1-3)
        postal_code = str(random.randint(11000, 38000))

        return {
            'street': f"{street_name} {street_number}",
            'city': city,
            'postal_code': postal_code,
            'full_address': f"{street_name} {street_number}, {city}"
        }

    @staticmethod
    def generate_email(name=None):
        """
        Generate a random email address.

        Args:
            name: Optional name to base email on

        Returns:
            str: Email address
        """
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

        if name:
            # Create email from name
            parts = name.lower().split()
            if len(parts) >= 2:
                username = f"{parts[0]}.{parts[1]}{random.randint(1, 999)}"
            else:
                username = f"{parts[0]}{random.randint(1, 999)}"
        else:
            username = f"user{random.randint(1000, 9999)}"

        domain = random.choice(domains)
        return f"{username}@{domain}"

    @staticmethod
    def generate_complete_profile():
        """
        Generate a complete profile with all information.

        Returns:
            dict: Complete profile data
        """
        gender = random.choice(['male', 'female'])
        name = SerbianDataGenerator.generate_name(gender)
        address = SerbianDataGenerator.generate_address()

        return {
            'name': name,
            'phone': SerbianDataGenerator.generate_phone(),
            'email': SerbianDataGenerator.generate_email(name),
            'address': address['full_address'],
            'street': address['street'],
            'city': address['city'],
            'postal_code': address['postal_code'],
            'gender': gender
        }


if __name__ == "__main__":
    # Demo usage
    print("Serbian Data Generator Demo\n")

    for i in range(5):
        profile = SerbianDataGenerator.generate_complete_profile()
        print(f"Profile {i+1}:")
        print(f"  Name: {profile['name']}")
        print(f"  Phone: {profile['phone']}")
        print(f"  Email: {profile['email']}")
        print(f"  Address: {profile['address']}")
        print(f"  City: {profile['city']}")
        print(f"  Postal Code: {profile['postal_code']}")
        print()
