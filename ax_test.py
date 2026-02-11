from ApplicationServices import (
    AXUIElementCreateSystemWide,
    AXUIElementCopyAttributeValue,
    kAXFocusedUIElementAttribute,
    kAXSelectedTextAttribute
)

def get_selected_text():
    system_wide = AXUIElementCreateSystemWide()

    err, focused_element = AXUIElementCopyAttributeValue(
        system_wide,
        kAXFocusedUIElementAttribute,
        None
    )

    if err != 0:
        print("Could not access focused UI element.")
        return None

    err, selected_text = AXUIElementCopyAttributeValue(
        focused_element,
        kAXSelectedTextAttribute,
        None
    )

    if err != 0:
        print("No selected text detected.")
        return None

    return selected_text


if __name__ == "__main__":
    text = get_selected_text()

    if text:
        print("Selected text:")
        print(text)
    else:
        print("Nothing selected or unsupported app.")