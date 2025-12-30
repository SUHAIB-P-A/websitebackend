import requests
import json
import random
import string

BASE_URL = "http://127.0.0.1:8000/api"

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def run_test():
    print("Starting Verification...")
    
    # 1. Admin Login
    print("\n1. Testing Admin Login...")
    resp = requests.post(f"{BASE_URL}/staff-login/", json={'login_id': 'admin', 'password': 'admin123'})
    if resp.status_code == 200:
        print("   Admin Login Success")
    else:
        print(f"   Admin Login Failed: {resp.status_code} {resp.text}")
        return

    # 2. Create Staff Members
    print("\n2. Creating 2 Staff Members...")
    staff1_data = {
        "name": "Staff One",
        "email": f"staff1_{random_string()}@test.com",
        "login_id": f"staff1_{random_string()}",
        "password": "password123",
        "active_status": True
    }
    staff2_data = {
        "name": "Staff Two",
        "email": f"staff2_{random_string()}@test.com",
        "login_id": f"staff2_{random_string()}",
        "password": "password123",
        "active_status": True
    }
    
    s1 = requests.post(f"{BASE_URL}/staff/", json=staff1_data)
    s2 = requests.post(f"{BASE_URL}/staff/", json=staff2_data)
    
    if s1.status_code == 201 and s2.status_code == 201:
        staff1_id = s1.json()['id']
        staff2_id = s2.json()['id']
        print(f"   Created Staff 1 (ID: {staff1_id}) and Staff 2 (ID: {staff2_id})")
    else:
        print(f"   Failed to create staff. S1: {s1.text}, S2: {s2.text}")
        return

    # 3. Create Students and Verify Allocation
    print("\n3. Testing Automatic Allocation (Least Load)...")
    
    # Create Student A
    email_a = f"stdA_{random_string()}@test.com"
    student_data = {"first_name": "Student", "last_name": "A", "email": email_a, "phone_number": "1234567890"}
    r1 = requests.post(f"{BASE_URL}/submit/", json=student_data)
    if r1.status_code != 201:
         print(f"Creating Student A failed: {r1.status_code} {r1.text}")
    
    # Create Student B
    email_b = f"stdB_{random_string()}@test.com"
    student_data['email'] = email_b
    r2 = requests.post(f"{BASE_URL}/submit/", json=student_data)
    if r2.status_code != 201:
         print(f"Creating Student B failed: {r2.status_code} {r2.text}")
    
    # Check allocation
    # Get students as admin
    all_students = requests.get(f"{BASE_URL}/submit/").json()
    
    # Find our students
    try:
        stdA = next(s for s in all_students if s['email'] == email_a)
        stdB = next(s for s in all_students if s['email'] == email_b)
        
        print(f"   Student A assigned to: {stdA.get('assigned_staff_name')} (ID: {stdA.get('assigned_staff')})")
        print(f"   Student B assigned to: {stdB.get('assigned_staff_name')} (ID: {stdB.get('assigned_staff')})")
        
        if stdA.get('assigned_staff') and stdB.get('assigned_staff'):
            print("   Allocation Success: Both assigned.")
            if stdA.get('assigned_staff') != stdB.get('assigned_staff'):
                 print("   Load Balancing Success: Assigned to different staff.")
            else:
                 print("   Note: Assigned to same staff.")
        else:
            print("   Allocation Failed.")
    except StopIteration:
        print("   Failed to find created students in the list.")
        return

    # 4. Verify Staff Restricted View
    print("\n4. Testing Staff Restricted View...")
    # Staff 1 should only see their assigned student
    headers_s1 = {'X-Staff-ID': str(staff1_id)}
    resp_s1 = requests.get(f"{BASE_URL}/submit/", headers=headers_s1)
    
    # Count how many assigned to s1 in total db
    expected_count = len([s for s in all_students if s['assigned_staff'] == staff1_id])
    actual_count = len(resp_s1.json())
    
    if actual_count == expected_count:
        print(f"   Staff 1 sees {actual_count} students (Expected: {expected_count}). View Restriction Works.")
    else:
        print(f"   Staff 1 sees {actual_count}, Expected {expected_count}. View Restriction Failed.")

    # 5. Delete Staff and Redistribute
    print("\n5. Testing Redistribution on Staff Deletion...")
    # Delete Staff 1
    requests.delete(f"{BASE_URL}/staff/{staff1_id}/")
    print(f"   Deleted Staff 1.")
    
    all_students_after = requests.get(f"{BASE_URL}/submit/").json()
    # Find previous Staff 1's students by ID
    reassigned_students = [s for s in all_students_after if s['id'] in [stdA['id'], stdB['id']]]
    
    for s in reassigned_students:
        print(f"   Student {s['email']} re-assigned to: {s.get('assigned_staff_name')} (ID: {s.get('assigned_staff')})")
        if s.get('assigned_staff') == staff2_id:
            print("   Redistribution Success: Moved to Staff 2.")
        else:
            print(f"   Redistribution Check: ID {s.get('assigned_staff')}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    run_test()
