"""
Trekking Management Application (TMA) - Demo Seeding Script
Programmatically populates the database with:
- Exactly 1 Admin: admin@tma.com / admin123
- 2 Staff Members (with StaffProfile records and mountain specializations)
- 8 Expeditions in varied statuses (Open, Approved, Pending, Closed, Completed)
- 5 Users / Trekkers (4 active, 1 blacklisted for testing moderation)
- Diverse bookings (Booked, Paid, Pending payment, Completed, and Cancelled)
- In-app notification alerts
"""

import os
import sys
from datetime import datetime, date, timedelta

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification
from cache import invalidate_trek_cache

def seed_demo_data():
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("SEEDING DEMO DATA FOR TREKKING MANAGEMENT APPLICATION (TMA)")
        print("=" * 70)

        # 1. Ensure programmatic database creation
        db.create_all()

        # 2. Reset existing data cleanly while preserving or re-creating admin
        print("Clearing previous demonstration records...")
        Booking.query.delete()
        Notification.query.delete()
        Trek.query.delete()
        StaffProfile.query.delete()
        User.query.delete()
        db.session.commit()

        # 3. Seed Single Admin
        print("\n[1/5] Seeding System Administrator...")
        admin = User(
            name="System Administrator",
            email="admin@tma.com",
            phone="+91 9999000000",
            role="admin",
            status="active"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.flush()
        print("  ✔ Admin created: admin@tma.com / admin123")

        # 4. Seed 2 Staff Members
        print("\n[2/5] Seeding 2 Staff Guides...")
        staff1 = User(
            name="Karan Negi",
            email="karan.staff@tma.com",
            phone="+91 9876500001",
            role="staff",
            status="active"
        )
        staff1.set_password("staff123")
        db.session.add(staff1)
        db.session.flush()

        profile1 = StaffProfile(
            user_id=staff1.id,
            contact_details="Manali Basecamp, Channel VHF 144.200",
            specialization="High Altitude Alpine Routes & Glacier Navigation",
            status="active"
        )
        db.session.add(profile1)

        staff2 = User(
            name="Maya Sharma",
            email="maya.staff@tma.com",
            phone="+91 9876500002",
            role="staff",
            status="active"
        )
        staff2.set_password("staff123")
        db.session.add(staff2)
        db.session.flush()

        profile2 = StaffProfile(
            user_id=staff2.id,
            contact_details="Rishikesh Operations Center, Phone +91 9876500002",
            specialization="Wilderness First Responder & Weather Risk Assessment",
            status="active"
        )
        db.session.add(profile2)
        db.session.flush()
        print(f"  ✔ Staff 1: {staff1.name} ({staff1.email} / staff123)")
        print(f"  ✔ Staff 2: {staff2.name} ({staff2.email} / staff123)")

        # 5. Seed 5 Trekker Users (4 active, 1 blacklisted)
        print("\n[3/5] Seeding 5 Users / Trekkers...")
        users_data = [
            ("Aarav Mehta", "aarav@example.com", "user123", "+91 9811100001", 28, "+91 9811199999", "Mumbai, Maharashtra", "active"),
            ("Sneha Patel", "sneha@example.com", "user123", "+91 9811100002", 25, "+91 9811199998", "Ahmedabad, Gujarat", "active"),
            ("Vikram Singh", "vikram@example.com", "user123", "+91 9811100003", 32, "+91 9811199997", "Jaipur, Rajasthan", "active"),
            ("Ananya Roy", "ananya@example.com", "user123", "+91 9811100004", 24, "+91 9811199996", "Kolkata, West Bengal", "active"),
            ("Rohit Verma", "rohit@example.com", "user123", "+91 9811100005", 29, "+91 9811199995", "Delhi, NCR", "blacklisted"),
        ]

        created_users = []
        for name, email, pwd, phone, age, emergency, addr, st in users_data:
            u = User(
                name=name,
                email=email,
                phone=phone,
                age=age,
                emergency_contact=emergency,
                address=addr,
                role="user",
                status=st
            )
            u.set_password(pwd)
            db.session.add(u)
            created_users.append(u)
        db.session.flush()

        for u in created_users:
            status_tag = "ACTIVE" if u.status == "active" else "BLACKLISTED"
            print(f"  ✔ User: {u.name} ({u.email} / user123) - [{status_tag}]")

        # 6. Seed 8 Treks in Varied Statuses
        print("\n[4/5] Seeding 8 Mountain Expeditions across varied statuses...")
        today = date.today()

        treks_data = [
            # 1. Open
            {
                'name': "Kedarkantha Winter Summit",
                'location': "Uttarakhand",
                'difficulty': "Moderate",
                'duration_days': 5,
                'total_slots': 20,
                'available_slots': 17,  # 3 booked below
                'assigned_staff_id': staff1.id,
                'status': "Open",
                'start_date': today + timedelta(days=4),
                'end_date': today + timedelta(days=9),
                'price': 9500.0,
                'description': "Classic winter snow trek climbing to a 12,500 ft summit with 360-degree views of Swargarohini, Bandarpoonch, and Black Peak.",
                'instructions': "High ankle waterproof trekking boots, 4 warm layers, gaiters, and crampons provided at base."
            },
            # 2. Open
            {
                'name': "Hampta Pass & Chandratal Crossing",
                'location': "Himachal Pradesh",
                'difficulty': "Hard",
                'duration_days': 6,
                'total_slots': 16,
                'available_slots': 15,  # 1 booked below
                'assigned_staff_id': staff2.id,
                'status': "Open",
                'start_date': today + timedelta(days=8),
                'end_date': today + timedelta(days=14),
                'price': 13500.0,
                'description': "Dramatic crossover trail moving from lush green Kullu pine forests across the 14,000 ft pass into barren Spiti lunar landscapes.",
                'instructions': "Trekking poles, moisture-wicking thermals, and valid ID for Spiti checkpoint mandatory."
            },
            # 3. Open
            {
                'name': "Valley of Flowers UNESCO Biosphere",
                'location': "Uttarakhand",
                'difficulty': "Easy",
                'duration_days': 4,
                'total_slots': 25,
                'available_slots': 22,  # 3 booked below
                'assigned_staff_id': staff1.id,
                'status': "Open",
                'start_date': today + timedelta(days=12),
                'end_date': today + timedelta(days=16),
                'price': 8000.0,
                'description': "Gentle alpine meadow valley filled with over 500 species of wildflowers, Himalayan birch, and sacred Hemkund Sahib lake.",
                'instructions': "Lightweight daypack, rain poncho, and comfortable walking shoes."
            },
            # 4. Approved
            {
                'name': "Chadar Frozen Zanskar River Expedition",
                'location': "Ladakh",
                'difficulty': "Hard",
                'duration_days': 9,
                'total_slots': 12,
                'available_slots': 12,
                'assigned_staff_id': staff2.id,
                'status': "Approved",
                'start_date': today + timedelta(days=25),
                'end_date': today + timedelta(days=34),
                'price': 28000.0,
                'description': "Unrivalled winter expedition walking over the frozen ice sheets of the gorge of the Zanskar River in sub-zero conditions.",
                'instructions': "Gumboots, -20C rated down jacket, thermal insoles, and strict medical clearance."
            },
            # 5. Approved (Unassigned staff)
            {
                'name': "Bhrigu Lake Glacial Meadow Trek",
                'location': "Manali, Himachal Pradesh",
                'difficulty': "Moderate",
                'duration_days': 4,
                'total_slots': 18,
                'available_slots': 18,
                'assigned_staff_id': None,
                'status': "Approved",
                'start_date': today + timedelta(days=30),
                'end_date': today + timedelta(days=34),
                'price': 7200.0,
                'description': "High altitude glacial lake that changes colors throughout the day, sacred to Maharishi Bhrigu.",
                'instructions': "Daypack, fleece jacket, sun protection, and energy snacks."
            },
            # 6. Pending
            {
                'name': "Roopkund Mystery Lake Trail",
                'location': "Uttarakhand",
                'difficulty': "Hard",
                'duration_days': 8,
                'total_slots': 15,
                'available_slots': 15,
                'assigned_staff_id': None,
                'status': "Pending",
                'start_date': today + timedelta(days=50),
                'end_date': today + timedelta(days=58),
                'price': 15000.0,
                'description': "High altitude tarn situated at 16,500 feet, surrounded by rock-strewn glaciers and snow-clad peaks.",
                'instructions': "Awaiting forestry permits and environmental committee inspection."
            },
            # 7. Closed
            {
                'name': "Kashmir Great Lakes Alpine Circuit",
                'location': "Sonamarg, Kashmir",
                'difficulty': "Hard",
                'duration_days': 7,
                'total_slots': 14,
                'available_slots': 0,
                'assigned_staff_id': staff1.id,
                'status': "Closed",
                'start_date': today + timedelta(days=15),
                'end_date': today + timedelta(days=22),
                'price': 16500.0,
                'description': "Pristine circuit spanning Vishansar, Kishansar, Gadsar, Satsar, and Gangabal lakes.",
                'instructions': "Registration closed due to full batch allotment."
            },
            # 8. Completed
            {
                'name': "Triund Ridge Weekend Trek",
                'location': "Dharamshala, Himachal Pradesh",
                'difficulty': "Easy",
                'duration_days': 2,
                'total_slots': 30,
                'available_slots': 25,
                'assigned_staff_id': staff2.id,
                'status': "Completed",
                'start_date': today - timedelta(days=25),
                'end_date': today - timedelta(days=23),
                'price': 3500.0,
                'description': "Gentle panoramic ridge facing the majestic Dhauladhar ranges on one side and the Kangra Valley on the other.",
                'instructions': "Expedition successfully concluded last month."
            }
        ]

        created_treks = []
        for td in treks_data:
            t = Trek(
                name=td['name'],
                location=td['location'],
                difficulty=td['difficulty'],
                duration_days=td['duration_days'],
                total_slots=td['total_slots'],
                available_slots=td['available_slots'],
                assigned_staff_id=td['assigned_staff_id'],
                status=td['status'],
                start_date=td['start_date'],
                end_date=td['end_date'],
                price=td['price'],
                description=td['description'],
                instructions=td['instructions'],
                is_started=(td['status'] == 'Completed')
            )
            db.session.add(t)
            created_treks.append(t)
        db.session.flush()

        for t in created_treks:
            staff_label = t.assigned_staff.name if t.assigned_staff else "None"
            print(f"  ✔ Trek #{t.id}: {t.name:<38} [{t.status:<9}] - Slots: {t.available_slots}/{t.total_slots} (Staff: {staff_label})")

        # 7. Seed Bookings & Notifications
        print("\n[5/5] Seeding Demonstration Bookings & Notifications...")

        t_keda = created_treks[0]  # Kedarkantha
        t_hamp = created_treks[1]  # Hampta
        t_flow = created_treks[2]  # Valley of Flowers
        t_triu = created_treks[7]  # Triund (Completed)

        u_aarav = created_users[0]
        u_sneha = created_users[1]
        u_vikram = created_users[2]
        u_ananya = created_users[3]

        bookings_data = [
            # Aarav: 2 spots on Kedarkantha (Paid)
            (u_aarav.id, t_keda.id, 2, "Booked", "Paid", today - timedelta(days=2)),
            # Aarav: 1 spot on Triund (Completed)
            (u_aarav.id, t_triu.id, 1, "Completed", "Paid", today - timedelta(days=28)),
            # Sneha: 1 spot on Hampta Pass (Paid)
            (u_sneha.id, t_hamp.id, 1, "Booked", "Paid", today - timedelta(days=1)),
            # Vikram: 1 spot on Kedarkantha (Pending payment)
            (u_vikram.id, t_keda.id, 1, "Booked", "Pending", today - timedelta(days=1)),
            # Ananya: 3 spots on Valley of Flowers (Paid)
            (u_ananya.id, t_flow.id, 3, "Booked", "Paid", today - timedelta(days=3)),
            # Ananya: 1 spot on Triund (Completed)
            (u_ananya.id, t_triu.id, 1, "Completed", "Paid", today - timedelta(days=27)),
        ]

        for uid, tid, count, b_status, p_status, b_date in bookings_data:
            b = Booking(
                user_id=uid,
                trek_id=tid,
                participants_count=count,
                status=b_status,
                payment_status=p_status,
                booking_date=b_date
            )
            db.session.add(b)

            # Corresponding Notification
            u_obj = db.session.get(User, uid)
            t_obj = db.session.get(Trek, tid)
            msg = f"Booking confirmed for '{t_obj.name}' ({count} participant(s)). Status: {b_status}."
            notif = Notification(user_id=uid, message=msg, created_at=b_date)
            db.session.add(notif)

        db.session.commit()
        print("  ✔ 6 bookings successfully seeded across users.")

        # Invalidate cache
        invalidate_trek_cache()

        print("\n" + "=" * 70)
        print("DEMO SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nQUICK LOGIN CREDENTIALS FOR TESTING:")
        print("  1. Admin:       admin@tma.com       / admin123  (Super Administrator)")
        print("  2. Staff 1:     karan.staff@tma.com / staff123  (Assigned: Kedarkantha, Valley of Flowers)")
        print("  3. Staff 2:     maya.staff@tma.com  / staff123  (Assigned: Hampta Pass, Chadar, Triund)")
        print("  4. Trekker 1:   aarav@example.com   / user123   (Active bookings: Kedarkantha)")
        print("  5. Trekker 2:   sneha@example.com   / user123   (Active bookings: Hampta Pass)")
        print("  6. Blacklisted: rohit@example.com   / user123   (Tests 403 login rejection)")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    seed_demo_data()
