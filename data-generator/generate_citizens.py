import random
import threading
from datetime import datetime, timedelta
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Database configurations
OLD_PENSION_DB_URL = "mysql+pymysql://admin:1234@localhost:3306/pension_db"
FOOD_DEPARTMENT_DB_URL = "mysql+pymysql://admin:1234@localhost:3306/food_ration_db"

# Define citizens table schema
metadata = MetaData()
citizens = Table(
    "citizens",
    metadata,
    Column("aadhar", String(12), primary_key=True),
    Column("name", String(100)),
    Column("age", Integer),
    Column("gender", String(10)),
    Column("caste", String(50)),
    Column("location", String(100)),
    Column("created_on", DateTime),
    Column("updated_on", DateTime),
)

 

# Generate unique Aadhaar numbers for both databases
def generate_unique_aadhaar(total_records, overlap_count):
    all_aadhaar = set()
    overlapping_aadhaar = set()

    # Generate overlapping Aadhaar numbers
    while len(overlapping_aadhaar) < overlap_count:
        aadhar = str(random.randint(100000000000, 999999999999))
        if aadhar not in all_aadhaar:
            overlapping_aadhaar.add(aadhar)
            all_aadhaar.add(aadhar)

    # Generate unique Aadhaar numbers for the remaining records
    while len(all_aadhaar) < total_records:
        aadhar = str(random.randint(100000000000, 999999999999))
        if aadhar not in all_aadhaar:
            all_aadhaar.add(aadhar)

    return list(all_aadhaar), list(overlapping_aadhaar)

# Clear the citizens table before inserting new data
def clear_old_data(engine_url):
    engine = create_engine(engine_url)
    connection = engine.connect()
    try:
        connection.execute(citizens.delete())
        print("Cleared old data from citizens table.")
    except Exception as e:
        print(f"Error clearing old data: {e}")
    finally:
        connection.close()

# Insert Aadhaar numbers into the database using threads
def insert_citizens_with_aadhaar_threaded(engine_url, aadhaar_list, shared_details=None):
    # Clear old data before inserting new records
    clear_old_data(engine_url)

    def insert_batch(batch):
        engine = create_engine(engine_url, poolclass=QueuePool, pool_size=10, max_overflow=5)
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            batch_data = []
            for aadhar in batch:
                if shared_details and aadhar in shared_details:
                    # Use shared details for overlapping Aadhaar numbers
                    batch_data.append(shared_details[aadhar])
                else:
                    # Generate random details for unique Aadhaar numbers
                    batch_data.append({
                        "aadhar": aadhar,
                        "name": f"Citizen_{random.randint(1, 1000000)}",
                        "age": random.randint(18, 99),
                        "gender": random.choice(["Male", "Female", "Other"]),
                        "caste": random.choice(["General", "OBC", "SC", "ST"]),
                        "location": random.choice(["CityA", "CityB", "CityC", "CityD"]),
                        "created_on": datetime.now() - timedelta(days=random.randint(0, 3650)),
                        "updated_on": datetime.now(),
                    })

            session.execute(citizens.insert(), batch_data)
            session.commit()
            print(f"Inserted {len(batch)} records in thread {threading.current_thread().name}.")
        except Exception as e:
            print(f"Error in thread {threading.current_thread().name}: {e}")
            session.rollback()
        finally:
            session.close()

    threads = []
    max_threads = 10  # Limit the number of threads
    batch_size = 1000
    for i in range(0, len(aadhaar_list), batch_size):
        batch = aadhaar_list[i:i + batch_size]
        while len(threads) >= max_threads:
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)

        thread = threading.Thread(target=insert_batch, args=(batch,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    total_old_pension_records = 20000
    total_food_department_records = 150000
    overlap_count = 10000

    print("Generating unique Aadhaar numbers...")
    all_aadhaar, overlapping_aadhaar = generate_unique_aadhaar(
        total_old_pension_records + total_food_department_records - overlap_count, overlap_count
    )

    # Generate shared details for overlapping Aadhaar numbers
    shared_details = {
        aadhar: {
            "aadhar": aadhar,
            "name": f"Citizen_{random.randint(1, 1000000)}",
            "age": random.randint(18, 99),
            "gender": random.choice(["Male", "Female", "Other"]),
            "caste": random.choice(["General", "OBC", "SC", "ST"]),
            "location": random.choice(["CityA", "CityB", "CityC", "CityD"]),
            "created_on": datetime.now() - timedelta(days=random.randint(0, 3650)),
            "updated_on": datetime.now(),
        }
        for aadhar in overlapping_aadhaar
    }

    print("Allocating Aadhaar numbers to Old Pension database...")
    old_pension_aadhaar = all_aadhaar[:total_old_pension_records]
    insert_citizens_with_aadhaar_threaded(OLD_PENSION_DB_URL, old_pension_aadhaar, shared_details)

    print("Allocating Aadhaar numbers to Food Department database...")
    food_department_aadhaar = all_aadhaar[total_old_pension_records:]
    insert_citizens_with_aadhaar_threaded(FOOD_DEPARTMENT_DB_URL, food_department_aadhaar, shared_details)

    print("Data generation completed.")