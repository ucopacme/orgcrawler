import organizer
import organizer.crawler

def test_crawler():
    response = organizer.crawler.hello_world()
    assert response == 'hello world'
