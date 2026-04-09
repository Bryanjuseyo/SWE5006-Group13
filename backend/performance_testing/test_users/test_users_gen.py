import csv

__test__ = False

NUM_USERS = 50


def main():
    with open("test_users.csv", "w", newline="") as f:
        writer = csv.writer(f)

        # header
        writer.writerow(["email", "password"])

        for i in range(1, NUM_USERS + 1):
            username = f"enduser{i}@test.com"
            password = "Password1"
            writer.writerow([username, password])


if __name__ == "__main__":
    main()
