import streamlit.testing.v1 as st_test

def test_run():
    app = st_test.AppTest.from_file("app.py")
    app.run()
    print("✅ the app run test passed!")