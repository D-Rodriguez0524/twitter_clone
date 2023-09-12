"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# tests to test for in User model similar to message view

# Does the repr method work as expected?
# Does is_following successfully detect when user1 is following user2?
# Does is_following successfully detect when user1 is not following user2?
# Does is_followed_by successfully detect when user1 is followed by user2?
# Does is_followed_by successfully detect when user1 is not followed by user2?
# Does User.create successfully create a new user given valid credentials?
# Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?
# Does User.authenticate successfully return a user when given a valid username and password?
# Does User.authenticate fail to return a user when the username is invalid?
# Does User.authenticate fail to return a user when the password is invalid?


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup('test1', 'test1@test.com', 'password', None)
        user1_id = 1111
        u1.id = user1_id

        u2 = User.signup('test2', 'test2@test.com', 'password', None)
        user2_id = 2222
        u2.id = user2_id

        db.session.commit()
        u1 = User.query.get(user1_id)
        u2 = User.query.get(user2_id)
        
        self.u1 = u1
        self.user1_id = user1_id

        self.u2 = u2
        self.user2_id = user2_id

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    """
    Following tests
    """

    def test_user_follows(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id,self.u1.id)
        self.assertEqual(self.u1.following[0].id,self.u2.id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    """
    Signup Tests
    """
    def test_valid_signup(self):
        u_test = User.signup("testing", "test@test.com", "password", None)
        user_id = 99999
        u_test.id = user_id
        db.session.commit()

        u_test = User.query.get(user_id)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "testing")
        self.assertEqual(u_test.email, "test@test.com")
        self.assertNotEqual(u_test.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        invalid = User.signup(None, "test@test.com", "password", None)
        user_id = 123456789
        invalid.id = user_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid = User.signup("testing", None, "password", None)
        user_id = 123789
        invalid.id = user_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testing", "test@test.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testing", "test@test.com", None, None)

    """
    Authenticate tests
    """
    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.user1_id)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))