import csv

NUM_USERS = 50

with open("test_users.csv", "w", newline="") as f:
    writer = csv.writer(f)
    
    # header
    writer.writerow(["email", "password"])
    
    for i in range(1, NUM_USERS + 1):
        username = f"enduser{i}@test.com"
        password = f"Password1"
        writer.writerow([username, password])