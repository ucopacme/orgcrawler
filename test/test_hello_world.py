import organizer
import organizer.hello_world


def test_hello_world():

    response = organizer.hello_world.hello_world()
    assert response == 'hello world'


def test_hello_eric():

    response = organizer.hello_world.hello_eric()
    assert response == 'hello eric'
