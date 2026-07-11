"""
delivery_fleet.py

Task 14B -- Mini Delivery Fleet OOP (Logistics variation of Lesson 14).
Standalone script demonstrating the same __init__/__str__/inheritance
pattern used in Task 14A's Patient class, applied to a delivery fleet.

Run with: python delivery_fleet.py
"""


class DeliveryVehicle:
    """A single vehicle in a logistics fleet, tracking its load and deliveries."""

    def __init__(self, vehicle_id, driver_name, max_capacity_kg):
        """
        Build a new DeliveryVehicle.

        Args:
            vehicle_id (str): unique fleet identifier. Stored UPPERCASE.
            driver_name (str): driver's full name. Stored Title Case.
            max_capacity_kg (float): maximum weight this vehicle can carry.
        """
        self.vehicle_id = vehicle_id.strip().upper()
        self.driver_name = driver_name.strip().title()
        self.max_capacity_kg = max_capacity_kg
        self.current_load_kg = 0
        self.deliveries = []

    def load(self, package_id, weight_kg):
        """
        Add a package to this vehicle if there's enough capacity remaining.

        Args:
            package_id (str): identifier for the package.
            weight_kg (float): weight of the package.

        Returns:
            bool: True if loaded successfully, False if rejected (overweight).
        """
        if self.current_load_kg + weight_kg > self.max_capacity_kg:
            print(f"❌ Overweight: {package_id} ({weight_kg}kg) exceeds capacity "
                  f"of {self.vehicle_id} (remaining: {self.capacity_remaining()}kg)")
            return False

        self.deliveries.append({"id": package_id, "weight": weight_kg})
        self.current_load_kg += weight_kg
        print(f"✅ Loaded {package_id} ({weight_kg}kg) onto {self.vehicle_id}")
        return True

    def capacity_remaining(self):
        """Return how many kg of capacity this vehicle has left."""
        return self.max_capacity_kg - self.current_load_kg

    def __str__(self):
        """Human-readable one-line fleet summary."""
        return (f"[{self.vehicle_id}] {self.driver_name} | "
                f"Load: {self.current_load_kg}/{self.max_capacity_kg}kg | "
                f"Packages: {len(self.deliveries)}")

    def __repr__(self):
        """Developer-facing representation for debugging."""
        return (f"DeliveryVehicle(vehicle_id={self.vehicle_id!r}, "
                f"driver_name={self.driver_name!r}, "
                f"max_capacity_kg={self.max_capacity_kg!r})")


class ExpressVehicle(DeliveryVehicle):
    """An express delivery vehicle -- IS-A DeliveryVehicle with a priority surcharge."""

    def __init__(self, vehicle_id, driver_name, max_capacity_kg, express_rate):
        """Build an ExpressVehicle, reusing DeliveryVehicle's setup via super()."""
        super().__init__(vehicle_id, driver_name, max_capacity_kg)
        self.express_rate = express_rate  # naira surcharge per kg

    def calculate_fee(self, weight_kg):
        """
        Calculate the delivery fee for a package, including the express surcharge.

        Args:
            weight_kg (float): weight of the package being quoted.

        Returns:
            str: formatted breakdown of base fee, express fee, and total in naira.
        """
        base_fee = weight_kg * 500
        express_fee = weight_kg * self.express_rate
        total = base_fee + express_fee
        return (f"Base: ₦{base_fee:,.2f} + Express: ₦{express_fee:,.2f} "
                f"= ₦{total:,.2f}")

    def __str__(self):
        """Overridden summary that reuses the parent's __str__ via super()."""
        return f"[EXPRESS] {super().__str__()} | Rate: ₦{self.express_rate}/kg"


def print_fleet_summary(fleet):
    """Print a formatted summary line for every vehicle in the fleet."""
    print("\n" + "=" * 60)
    print("FLEET SUMMARY")
    print("=" * 60)
    for vehicle in fleet:
        print(vehicle)  # calls __str__ (overridden version for ExpressVehicle)
    total_packages = sum(len(v.deliveries) for v in fleet)
    total_load = sum(v.current_load_kg for v in fleet)
    print("-" * 60)
    print(f"Total vehicles: {len(fleet)} | Total packages: {total_packages} "
          f"| Total load: {total_load}kg")
    print("=" * 60)


def main():
    """Create a fleet, load packages, demonstrate rejection, print summary."""

    # ------------------------------------------------------------------
    # 1. Create at least 3 fleet vehicles
    # ------------------------------------------------------------------
    van = DeliveryVehicle("van-001", "emeka dike", 1000)
    bike = DeliveryVehicle("bike-002", "amaka obi", 50)
    express = ExpressVehicle("exp-001", "bisi adeyemi", 500, express_rate=200)

    fleet = [van, bike, express]

    # ------------------------------------------------------------------
    # 2. Load packages onto each vehicle
    # ------------------------------------------------------------------
    print("--- Loading packages ---")
    van.load("PKG-A", 300)
    van.load("PKG-B", 400)
    bike.load("PKG-C", 15)
    express.load("PKG-D", 25)

    # ------------------------------------------------------------------
    # 3. Demonstrate overloading rejection
    # ------------------------------------------------------------------
    print("\n--- Attempting an overweight load (should be rejected) ---")
    van.load("PKG-E", 800)     # 300 + 400 + 800 > 1000 -> rejected
    bike.load("PKG-F", 40)     # 15 + 40 > 50 -> rejected

    # ------------------------------------------------------------------
    # 4. Show the express fee calculation
    # ------------------------------------------------------------------
    print("\n--- Express fee quote ---")
    print(express.calculate_fee(25))

    # ------------------------------------------------------------------
    # 5. Print the fleet summary
    # ------------------------------------------------------------------
    print_fleet_summary(fleet)

    # A quick isinstance check, same IS-A idea as PaediatricPatient/Patient
    print("\nisinstance(express, DeliveryVehicle):", isinstance(express, DeliveryVehicle))
    print("isinstance(van, ExpressVehicle):", isinstance(van, ExpressVehicle))


if __name__ == "__main__":
    main()
