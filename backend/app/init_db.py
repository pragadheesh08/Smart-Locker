
from app.auth.db import User
from app.db import Base, SessionLocal, engine
from app.lockers.db import Locker


def initialize_database():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        user = db.query(User).filter_by(user_id="DEMO_USER").first()

        if user is None:
            db.add(
                User(
                    user_id="DEMO_USER",
                    display_name="Demo User",
                    is_active=True,
                )
            )

        for code, allot in (
            ("L01", "allotted_locked"), 
            ("L02", "unallotted"), 
            ("L03", "unallotted"),
        ):
            rcode = f"R01/{code}"
            locker = (
                db.query(Locker)
                .filter_by(locker_id=rcode)
                .first()
            )

            if locker is None:
                db.add(
                    Locker(
                        locker_id=rcode,
                        allocated_user_id="DEMO_USER" if allot == "allotted_locked" else None,
                        state=allot,
                    )
                )

        db.commit()


if __name__ == "__main__":
    initialize_database()
