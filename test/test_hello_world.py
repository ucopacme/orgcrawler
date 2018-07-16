import organizer
import organizer.hello_world

def test_crawler():
    response = organizer.hello_world.hello_world()
    assert response == 'hello world'
