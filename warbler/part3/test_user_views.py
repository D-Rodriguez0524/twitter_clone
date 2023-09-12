"""user view test"""

# run these tests like:
#
#    python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes, connect_db

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Testing views for messages"""

    def setUp(self):
        """create test client, add simple data"""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="pass123",
                                    image_url=None)
        self.testuser_id = 1111
        self.testuser.id = self.testuser_id

        self.u1 = User.signup('user1', 'user1@test.com', 'password1', None)
        self.u1_id = 222
        self.u1.id=self.u1_id
        self.u2 = User.signup('user2', 'user2@test.com', 'password2', None)
        self.u2_id = 333
        self.u2.id=self.u2_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp 
    
    def test_users_index(self):
        """testing if all users show"""
        with self.client as c:
            resp = c.get('/users')

            self.assertIn('@testuser', str(resp.data))
            self.assertIn('@user1', str(resp.data))
            self.assertIn('@user2', str(resp.data))

    def test_user_show(self):
        """testing if user shows """
        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}')

            self.assertEqual(resp.status_code,200)
            self.assertIn('@testuser', str(resp.data))

    """
        Testing view functions for followers and following routes
    """

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

            
    def test_show_following(self):
        
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@user1", str(resp.data))
            self.assertIn("@user2", str(resp.data))
            

    def test_show_followers(self):
        
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@user1", str(resp.data))
            self.assertNotIn("@user2", str(resp.data))

    """
        Testing unauthorized access to followers and following pages
    """

    def test_unauthorized_following_page_access(self):
        
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@user1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):

        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@user1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    """
        Testing likes feature
    """

    def setup_likes(self):
        m1 = Message(text="message 1", user_id=self.testuser_id)
        m2 = Message(text="message 2", user_id=self.testuser_id)
        m3 = Message(id=123, text="likable warble", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=123)

        db.session.add(l1)
        db.session.commit()

    def test_add_likes(self):
        
        m = Message(id=1234, text = "testing", user_id = self.u1_id)
        
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

                resp = c.post('/messages/1234/likes', follow_redirects=True)
                self.assertEqual(resp.status_code, 200)

                likes = Likes.query.filter(Likes.message_id==1234).all()
                self.assertEqual(len(likes), 1)
                self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        like = Likes.query.filter(
            Likes.user_id==self.testuser_id and Likes.message_id==m.id
        ).one()

        # Now we are sure that testuser likes the message "likable warble"
        self.assertIsNotNone(like)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/messages/{m.id}/likes", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            # the like has been deleted
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/likes", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())



            
