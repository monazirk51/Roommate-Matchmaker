import pandas as pd
import random
import numpy as np
import os

NUM_STUDENTS = 200
FILENAME = "hostel_users_clustered.csv"

first_names_male   = ["Aarav","Vivaan","Aditya","Vihaan","Arjun","Sai","Reyansh","Ayaan",
                       "Krishna","Ishaan","Rohan","Karan","Dev","Nikhil","Rahul","Yash",
                       "Pranav","Aman","Kunal","Harsh"]
first_names_female = ["Diya","Saanvi","Ananya","Aadhya","Pari","Kiara","Naira","Myra",
                       "Riya","Meera","Priya","Sneha","Pooja","Nisha","Kavya","Tanvi",
                       "Shreya","Ankita","Divya","Simran"]
last_names  = ["Sharma","Verma","Gupta","Malhotra","Singh","Kumar","Mehta","Reddy","Patel","Joshi"]
majors      = ["CSE","ECE","Mech","Civil","IT","AI&DS"]
areas       = ["Koramangala","Indiranagar","HSR Layout","Whitefield","BTM Layout","Marathahalli"]
rent_ranges = [(3000,5000),(5000,8000),(8000,12000),(12000,20000)]
rent_labels = ["Rs.3K-5K","Rs.5K-8K","Rs.8K-12K","Rs.12K-20K"]
food_opts   = ["Vegetarian","Non-Vegetarian","Eggetarian"]

data = []
print(f"Generating {NUM_STUDENTS} student profiles...")

for i in range(NUM_STUDENTS):
    gender = random.choice(["Male","Female"])
    name   = f"{random.choice(first_names_male if gender=='Male' else first_names_female)} {random.choice(last_names)}"
    major  = random.choice(majors)
    contact= f"+91 {random.randint(6000000000, 9999999999)}"
    area   = random.choice(areas)
    ri     = random.randint(0,3)
    rent   = random.randint(*rent_ranges[ri])
    food   = random.choice(food_opts)
    room_capacity = random.randint(1,3)

    ct = random.choice([0,1,2,3])
    if   ct==0: sleep,clean,social,noise = random.randint(1,3),random.randint(7,10),random.randint(1,3),random.randint(1,3)
    elif ct==1: sleep,clean,social,noise = random.randint(8,10),random.randint(1,5),random.randint(8,10),random.randint(7,10)
    elif ct==2: sleep,clean,social,noise = random.randint(1,4),random.randint(6,9),random.randint(7,9),random.randint(4,7)
    else:       sleep,clean,social,noise = random.randint(9,10),random.randint(3,7),random.randint(1,4),random.randint(1,5)

    sleep = int(np.clip(sleep + random.uniform(-0.5,0.5), 1, 10))
    data.append([i+1000, name, gender, major, contact, area,
                 rent, rent_labels[ri], food, room_capacity,
                 sleep, clean, social, noise])

cols = ["ID","Name","Gender","Major","Contact","Area",
        "Monthly_Rent","Rent_Label","Food_Preference","Room_Capacity",
        "Sleep","Cleanliness","Social","Noise"]
df = pd.DataFrame(data, columns=cols)
df.to_csv(FILENAME, index=False)
print(f"Done. {len(df)} rows written to {FILENAME}")
