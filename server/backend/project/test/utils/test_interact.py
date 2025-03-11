from project.interact.utils import extract_context, load_history, validate_file_extension, raw, record_exchange

# pytest project/test/utils/test_interact.py -v -s
def test_raw():
    assert raw({"role": "user", "content": "hello"}) == "user: hello\n"
    assert raw({"role": "assistant", "content": "hello"}) == "assistant: hello\n"
    assert raw({"role": "user", "content": ""}) == "user: \n"
    assert raw({"role": "assistant", "content": ""}) == "assistant: \n"

def test_extract_context():
    message = "Hello"
    history = [{"role": "user", "content": "Hi"}]
    result = extract_context(message, history, 100)
    assert result == "user: Hi\nuser: Hello\n"
    history = [{"role": "user", "content": "Hi"}, 
               {"role": "assistant", "content": "Hello"}, 
               {"role": "user", "content": "How are you?"}, 
               {"role": "assistant", "content": "I am good. How can I help?"}, 
               {"role": "user", "content": "nevermind."}, {"role": "assistant", "content": "Have a great day!"}]
    result = extract_context(message, history, 1000)
    assert result == "user: Hi\nassistant: Hello\nuser: How are you?\nassistant: I am good. How can I help?\nuser: nevermind.\nassistant: Have a great day!\nuser: Hello\n"
    
    result = extract_context(message,history,100)
    assert result == "assistant: I am good. How can I help?\nuser: nevermind.\nassistant: Have a great day!\nuser: Hello\n"
    
    history = [{"role": "user", "content": "Hi"}, 
               {"role": "assistant", "content": "Hello"}, 
               {"role": "user", "content": "I am feeling fine. I don't like writing long tests. This is very tedious, especially when I'm writing a test that's very long. I tend to just repeat myself over and over and over again. I wonder how many characters this is."},
               {"role": "assistant", "content": "I'm sorry to hear that!"}
            ]
    result = extract_context(message, history, 180)
    assert result == "user: I am feeling fine. I don't like writing long tests. This is very tedious, especially when I'm writing a test that's very long.\nassistant: I'm sorry to hear that!\nuser: Hello\n"

def test_load_history():
    rows = [(1, '{"messages": [{"role": "user", "content": "Hi"}]}')]
    result = load_history(rows)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Hi"
    rows = [
        (1, '{"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]}'),
        (2, '{"messages": [{"role": "user", "content": "How are you?"}, {"role": "assistant", "content": "I am good. How can I help?"}]}'),
        (3, '{"messages": [{"role": "user", "content": "nevermind."},{"role": "assistant", "content": "Have a great day!"}]}')
    ]
    result = load_history(rows)
    assert len(result) == 6
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Hi"
    assert result[1]["role"] == "assistant"
    assert result[1]["content"] == "Hello"
    assert result[2]["role"] == "user"
    assert result[2]["content"] == "How are you?"
    assert result[3]["role"] == "assistant"
    assert result[3]["content"] == "I am good. How can I help?"
    assert result[4]["role"] == "user"
    assert result[4]["content"] == "nevermind."
    assert result[5]["role"] == "assistant"
    assert result[5]["content"] == "Have a great day!"

def test_validate_file_extension():
    assert validate_file_extension("document.txt") is True
    assert validate_file_extension("document.odt") is True
    assert validate_file_extension("document.docx") is True
    assert validate_file_extension("document.pdf") is False
