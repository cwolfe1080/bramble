import curses
import textwrap
import time
import sys

# Windows-specific keybindings (ASCII control codes)
KEY_EXIT = 24           # Ctrl+X
KEY_SAVE = 23           # Ctrl+W
KEY_SAVE_AS = 5         # Ctrl+E
KEY_OPEN = 15           # Ctrl+O
KEY_TOGGLE_TIME = 20    # Ctrl+T
KEY_WORD_GOAL = 7       # Ctrl+G
KEY_CHAPTER = 14        # Ctrl+N
KEY_OUTLINE = 12        # Ctrl+L
KEY_IMPORT_EXPORT = 9   # Ctrl+I
KEY_JUMP_TO_LINE = 11   # Ctrl+K
KEY_HELP = 10           # Ctrl+J


# \n

# Initialize state
current_filename = ''
scroll_offset = 0
modified = False
time_24h = True
word_goal = 0
metadata = {}

def save_to_file(buffer, filename):
    global metadata, word_goal, time_24h
    metadata['g'] = word_goal
    metadata['t'] = time_24h
    with open(filename + '.txt', "w") as f:
        # Write metadata
        f.write("::metadata::\n")
        for key, value in metadata.items():
            if key == 'c' and isinstance(value, list):
                for line_num in value:
                    f.write(f"c: {line_num}\n")
            else:
                f.write(f"{key}: {value}\n")
        f.write("::end::\n")
        # Write content
        for line in buffer:
            f.write(line + "\n")

def load_from_file(filename):
    global metadata, word_goal, time_24h
    metadata = {}
    
    try:
        with open(filename + '.txt', "r") as f:
            lines = f.readlines()

        # Metadata detection
        content_start = 0
        if lines and lines[0].strip() == "::metadata::":
            for i, line in enumerate(lines[1:], 1):
                stripped = line.strip()
                if stripped == "::end::":
                    content_start = i + 1
                    break
                # Parse metadata line
                if ':' in stripped:
                    key, value = stripped.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Handle chapter lines separately
                    if key == 'c':
                        if 'c' not in metadata:
                            metadata['c'] = []
                        try:
                            metadata['c'].append(int(value))
                        except ValueError:
                            pass
                    elif key == 'g':
                        try:
                            metadata['g'] = int(value)
                            word_goal = metadata['g']
                        except ValueError:
                            word_goal = 0
                    elif key == 't':
                        time_24h = value.lower() == 'true'
                        metadata['t'] = time_24h

        
        # Load actual buffer
        return [line.rstrip("\n") for line in lines[content_start:]]

    except FileNotFoundError:
        return ['']

                            
def move_cursor(direction, buffer, cursor_y, cursor_x):
    if direction == 'left':
        if cursor_x > 0:
            return cursor_y, cursor_x - 1
        elif cursor_y > 0:
            return cursor_y - 1, len(buffer[cursor_y - 1])
    elif direction == 'right':
        if cursor_x < len(buffer[cursor_y]):
            return cursor_y, cursor_x + 1
        elif cursor_y + 1 < len(buffer):
            return cursor_y + 1, 0
    elif direction == 'up':
        if cursor_y > 0:
            return cursor_y - 1, min(cursor_x, len(buffer[cursor_y - 1]))
    elif direction == 'down':
        if cursor_y + 1 < len(buffer):
            return cursor_y + 1, min(cursor_x, len(buffer[cursor_y + 1]))
    return cursor_y, cursor_x

def prompt_filename(stdscr, prompt_msg):
    stdscr.clear()
    curses.echo()
    stdscr.addstr(0, 0, prompt_msg)
    stdscr.addstr(3, 0, "Leave blank to cancel")
    stdscr.refresh()
    filename = stdscr.getstr(1, 0, 60).decode('utf-8')
    curses.noecho()
    return filename

def show_popup(stdscr, message, width, height):
    h, w = stdscr.getmaxyx()
    win = curses.newwin(height, width, (h - height) // 2, (w - width) // 2)
    win.box()
    win.addstr(2, 2, message[:width - 4])
    win.refresh()
    stdscr.getch()
    win.clear()
    stdscr.refresh()

def show_help_menu(stdscr):
    help_text = [
        "Bramble Help Menu",
        "",
        "Ctrl+E   → Save As (Names and saves the buffer)",
        "Ctrl+W   → Save (Saves the buffer to the current filename)",
        "Ctrl+O   → Open a document",
        "Ctrl+T   → Toggle time format",
        "Ctrl+G   → Set word goal",
        "Ctrl+N   → Mark line as chapter title",
        "Ctrl+L   → Open outline",
        "Ctrl+I   → Open the import/export menu",
        "Ctrl+K   → Jump to line",
        "Ctrl+H   → Show this help menu",
        "Ctrl+X   → Exit",
        "Arrow Keys → Move cursor",
        "",
        "See github.com/cwolfe1080/bramble.git for more info",
        "",
        "Press any key to return to editing..."
    ]
    h, w = stdscr.getmaxyx()
    win_height = len(help_text) + 2
    win_width = max(len(line) for line in help_text) + 4
    win = curses.newwin(win_height, win_width, (h - win_height) // 2, (w - win_width) // 2)
    win.box()
    for i, line in enumerate(help_text):
        win.addstr(i + 1, 2, line)
    win.refresh()
    win.getch()
    win.clear()
    stdscr.refresh()

def draw_status_bar(stdscr, filename, buffer, cursor_y, cursor_x):
    global time_24h, word_goal
    h, w = stdscr.getmaxyx()
    name = filename if filename else "Untitled"
    word_count = sum(len(line.split()) for line in buffer)
    new_word_goal = ' / ' + str(word_goal) if word_goal > 0 else ""
    clock = time.strftime("%H:%M") if time_24h else time.strftime("%I:%M %p")
    mod_marker = "*" if modified else ""
    status = f" {name}{mod_marker} - Words: {word_count}{new_word_goal} - Ln {cursor_y+1}, Col {cursor_x+1} - {clock} "
    stdscr.attron(curses.A_REVERSE)
    stdscr.addstr(h - 1, 0, status[:w-1])
    pad_width = max(0, w - len(status) - 1)
    stdscr.addstr(h - 1, len(status), " " * pad_width)
    stdscr.attroff(curses.A_REVERSE)

def confirm_exit(stdscr):
    h, w = stdscr.getmaxyx()
    win = curses.newwin(5, 50, (h - 5) // 2, (w - 50) // 2)
    win.box()
    win.addstr(2, 2, "Unsaved changes. Exit anyway? (Y/N)")
    win.refresh()
    while True:
        ch = win.getch()
        if ch in (ord('y'), ord('Y')):
            return True
        elif ch in (ord('n'), ord('N')):
            return False

def mark_chapter(cursor_line, stdscr):
    global metadata

    if 'c' not in metadata:
        metadata['c'] = []

    if cursor_line not in metadata['c']:
        metadata['c'].append(cursor_line)
        show_popup(stdscr, f'Line {cursor_line + 1} marked as chapter.', 50, 5)
    else:
        metadata['c'].remove(cursor_line)
        show_popup(stdscr, f'Line {cursor_line + 1} unmarked as chapter.', 50, 5)

def show_outline_menu(stdscr, buffer):
    global metadata

    if 'c' not in metadata or not metadata['c']:
        show_popup(stdscr, "No chapters marked.", 40, 5)
        return None

    # Prepare outline entries
    entries = []
    for line_num in sorted(metadata['c']):
        if 0 <= line_num < len(buffer):
            title = buffer[line_num].strip()
            entries.append(f"{len(entries)+1}. {title}")
        else:
            entries.append(f"{len(entries)+1}. (Invalid)")

    # Menu dimensions
    h, w = stdscr.getmaxyx()
    win_height = len(entries) + 4
    min_width= 40
    win_width = max(min_width, max(len(line) for line in entries) + 6)                    
    win = curses.newwin(win_height, win_width, (h - win_height) // 2, (w - win_width) // 2)
    win.box()
    win.addstr(1, 2, "Outline Menu")

    for i, line in enumerate(entries):
        win.addstr(i + 2, 2, line[:win_width - 4])
        
    win.refresh()
    key = win.getch()
    choice = key - ord('1')

    if 0 <= choice < len(metadata['c']):
        return sorted(metadata['c'])[choice]
    return None

def import_export_menu(stdscr, buffer):
    options = [
        "1. Export clean version (no metadata)",
        "2. Import plain text file",
        "Any other key to cancel"
    ]

    h, w = stdscr.getmaxyx()
    win_height = len(options) + 4
    win_width = max(len(line) for line in options) + 6
    win = curses.newwin(win_height, win_width, (h - win_height) // 2, (w - win_width) // 2)
    win.box()
    win.addstr(1, 2, "Choose an option:")

    for i, line in enumerate(options):
        win.addstr(i + 2, 2, line)

    win.refresh()
    key = win.getch()

    if key == ord('1'):
        name = prompt_filename(stdscr, "Export clean as:")
        if name:
            export_clean(buffer, name)
            show_popup(stdscr, f"Exported {name}_clean.txt", 50, 5)
    elif key == ord('2'):
        name = prompt_filename(stdscr, "Import plain text file:")
        if name:
            return import_plain_text(name)

    win.clear()
    stdscr.refresh()
    return None

def export_clean(buffer, filename):
    with open(filename + '_clean.txt', 'w') as f:
        for line in buffer:
            f.write(line + "\n")            

def import_plain_text(filename):
    try: 
        with open(filename + '.txt', 'r') as f:
            return [line.rstrip("\n") for line in f.readlines()]
    except FileNotFoundError:
        return ['']        



def main(stdscr):
    global current_filename, scroll_offset, modified, time_24h, word_goal
    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    height -= 1
    buffer = ['']
    cursor_y, cursor_x = 0, 0
    try:
        if len(sys.argv) > 1:
    	    filename = sys.argv[1]
    	    current_filename = filename
    	    buffer = load_from_file(filename)
    	    modified = False
        else:
    	    buffer = ['']
    except FileNotFoundError:
        show_popup(stdscr, "File not found", 30, 5)


    while True:
        key = stdscr.getch()

        if key == KEY_EXIT:  # Ctrl+X
            if modified and not confirm_exit(stdscr):
                continue
            break

        elif key == KEY_WORD_GOAL: # Ctrl+G
            try:
                new_goal = prompt_filename(stdscr, "Set word goal: ")
                if new_goal:
                    word_goal = int(new_goal)
                    modified = True
                else:
                    word_goal = 0
            except ValueError:
                show_popup(stdscr, "Invalid number", 40, 5)

        elif key == KEY_HELP:  # Ctrl+J
            show_help_menu(stdscr)

        elif key in (10, 13):  # Enter
            line = buffer[cursor_y]
            before = line[:cursor_x]
            after = line[cursor_x:]
            buffer[cursor_y] = before
            buffer.insert(cursor_y + 1, after)
            cursor_y += 1
            cursor_x = 0
            modified = True

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if cursor_x > 0:
                line = buffer[cursor_y]
                buffer[cursor_y] = line[:cursor_x - 1] + line[cursor_x:]
                cursor_x -= 1
                modified = True
            elif cursor_y > 0:
                current_line = buffer.pop(cursor_y)
                cursor_y -= 1
                cursor_x = len(buffer[cursor_y])
                buffer[cursor_y] += current_line
                modified = True

        elif key == KEY_SAVE_AS:  # Ctrl+E
            name = prompt_filename(stdscr, "Name document: ")
            if name:
                current_filename = name
                save_to_file(buffer, current_filename)
                modified = False

        elif key == KEY_SAVE:  # Ctrl+W
            if current_filename:
                save_to_file(buffer, current_filename)
                modified = False
                show_popup(stdscr, f"Saved {current_filename}", 50, 5)
            else:
                show_popup(stdscr, "No filename set. Use Save As (Ctrl+E) first.", 50, 5)

        elif key == KEY_OPEN:  # Ctrl+O
            name = prompt_filename(stdscr, "Load document: ")
            if name:
                current_filename = name
                buffer = load_from_file(name)
                cursor_y, cursor_x = 0, 0
                scroll_offset = 0
                modified = False

        elif key == KEY_CHAPTER: # Ctrl+N
            mark_chapter(cursor_y, stdscr)
            modified = True

        elif key == KEY_TOGGLE_TIME: # Ctrl+T
            time_24h = not time_24h
            modified = True

        elif key == KEY_OUTLINE: #Ctrl+L
            result = show_outline_menu(stdscr, buffer)
            if result is not None:
                cursor_y = result
                cursor_x = 0

        elif key == KEY_IMPORT_EXPORT: # Ctrl+I
            result = import_export_menu(stdscr, buffer)
            if result is not None:
                buffer = result
                cursor_y, cursor_x = 0, 0
                scroll_offset = 0
                modified = True

        elif  key == KEY_JUMP_TO_LINE: # Ctrl+K
            try:
                jump = prompt_filename(stdscr, "Jump to line: ")
                if jump:
                    cursor_y = int(jump) - 1
            except ValueError:
                show_popup(stdscr, "Invalid number", 40, 5)
            except IndexError:
                show_popup(stdscr, "Line does not exist", 40, 5)

            
        elif key == curses.KEY_LEFT:
            cursor_y, cursor_x = move_cursor('left', buffer, cursor_y, cursor_x)
        elif key == curses.KEY_RIGHT:
            cursor_y, cursor_x = move_cursor('right', buffer, cursor_y, cursor_x)
        elif key == curses.KEY_UP:
            cursor_y, cursor_x = move_cursor('up', buffer, cursor_y, cursor_x)
        elif key == curses.KEY_DOWN:
            cursor_y, cursor_x = move_cursor('down', buffer, cursor_y, cursor_x)

        elif 32 <= key <= 126:
            line = buffer[cursor_y]
            buffer[cursor_y] = line[:cursor_x] + chr(key) + line[cursor_x:]
            cursor_x += 1
            modified = True

            if len(buffer[cursor_y]) > width:
                long_line = buffer.pop(cursor_y)
                wrapped = textwrap.wrap(long_line, width)
                buffer[cursor_y:cursor_y] = wrapped
                cursor_y += len(wrapped) - 1
                cursor_x = len(wrapped[-1])

        # Clamp cursor
        cursor_y = max(0, min(cursor_y, len(buffer) - 1))
        cursor_x = max(0, min(cursor_x, len(buffer[cursor_y])))

        # Scroll logic
        if cursor_y < scroll_offset:
            scroll_offset = cursor_y
        elif cursor_y >= scroll_offset + height:
            scroll_offset = cursor_y - height + 1
        scroll_offset = max(0, min(scroll_offset, len(buffer) - height))

        stdscr.clear()
        draw_status_bar(stdscr, current_filename, buffer, cursor_y, cursor_x)
        for i, line in enumerate(buffer[scroll_offset : scroll_offset + height]):
            stdscr.addstr(i, 0, line[:width])
        try:
            stdscr.move(cursor_y - scroll_offset, cursor_x)
        except curses.error:
            pass
        stdscr.refresh()

curses.wrapper(main)

