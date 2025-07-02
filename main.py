import curses
import textwrap
import time

# Initialize variables:
current_filename = ''

def save_to_file(buffer, filename):
    with open(filename, "w") as f:
        for line in buffer:
            f.write(line + "\n")

def load_from_file(filename):
    try:
        with open(filename, "r") as f:
            return [line.rstrip("\n") for line in f.readlines()]
    except FileNotFoundError:
        return ['']

def move_cursor(direction, buffer, cursor_y, cursor_x):
    if direction == 'left':
        if cursor_x > 0:
            return cursor_y, cursor_x - 1
        elif cursor_y > 0:
            return cursor_y - 1, len(buffer[cursor_y - 1])
        else:
            return cursor_y, cursor_x

    elif direction == 'right':
        if cursor_x < len(buffer[cursor_y]):
            return cursor_y, cursor_x + 1
        elif cursor_y + 1 < len(buffer):
            return cursor_y + 1, 0
        else:
            return cursor_y, cursor_x

    elif direction == 'up':
        if cursor_y > 0:
            new_y = cursor_y - 1
            new_x = min(cursor_x, len(buffer[new_y]))
            return new_y, new_x
        else:
            return cursor_y, cursor_x

    elif direction == 'down':
        if cursor_y + 1 < len(buffer):
            new_y = cursor_y + 1
            new_x = min(cursor_x, len(buffer[new_y]))
            return new_y, new_x
        else:
            return cursor_y, cursor_x

    return cursor_y, cursor_x  # fallback

def prompt_filename(stdscr, prompt_msg):
    stdscr.clear()
    curses.echo()
    stdscr.addstr(0, 0, prompt_msg)
    stdscr.addstr(3, 0, "Leave blank to cancel")
    stdscr.clrtoeol()
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
    return

def draw_status_bar(stdscr, filename, buffer, cursor_y, cursor_x):
    h, w = stdscr.getmaxyx()
    name = filename if filename else "Untitled"
    word_count = sum(len(line.split()) for line in buffer)
    clock = time.strftime("%H:%M")
    status = f" {name} - Words: {word_count} - Ln {cursor_y+1}, Col {cursor_x+1} - {clock} "
    stdscr.attron(curses.A_REVERSE)
    stdscr.addstr(h - 1, 0, status[:w-1])
    stdscr.addstr(h - 1, len(status), " " * (w - len(status) - 1))
    stdscr.attroff(curses.A_REVERSE)
    
def main(stdscr):
    global current_filename
    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    usable_height = height - 1 # Leave the last line open for the status bar
    buffer = ['']
    cursor_y, cursor_x = 0, 0

    while True:
        key = stdscr.getch()

        if key == 24:  # Ctrl + X to exit
            h, w = stdscr.getmaxyx()
            win = curses.newwin(5, 50, (h - 5) // 2, (w - 50) // 2)
            win.box()
            win.addstr(2, 2, "Exiting..."[:50 - 4])
            win.refresh()
            break

        elif key in (10, 13):  # Enter
            buffer.insert(cursor_y + 1, '')
            cursor_y += 1
            cursor_x = 0

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if cursor_x > 0:
                line = buffer[cursor_y]
                buffer[cursor_y] = line[:cursor_x - 1] + line[cursor_x:]
                cursor_x -= 1
            elif cursor_y > 0:
                current_line = buffer.pop(cursor_y)
                cursor_y -= 1
                cursor_x = len(buffer[cursor_y])
                buffer[cursor_y] += current_line

        elif key == 5: # Ctrl+E to save as
            name = prompt_filename(stdscr, "Name document: ")
            if name == '':
                continue
            current_filename = name
            save_to_file(buffer, current_filename)

        elif key == 23:  # Ctrl+W to save
            if current_filename == '':
                show_popup(stdscr, "No filename set. Use Save As (Ctrl+E) first.", 50, 5)
            else:
                save_to_file(buffer, current_filename)
                name = "Saved " + current_filename
                show_popup(stdscr, name, 50, 5)

        elif key == 15:  # Ctrl+O to load
            name = prompt_filename(stdscr, "Load document: ")
            if name == '':
                continue
            current_filename = name
            buffer = load_from_file(name)
            cursor_y, cursor_x = 0, 0

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

            if len(buffer[cursor_y]) > width:
                long_line = buffer.pop(cursor_y)
                wrapped = textwrap.wrap(long_line, width)
                buffer[cursor_y:cursor_y] = wrapped
                cursor_y += len(wrapped) - 1
                cursor_x = len(wrapped[-1])

        # Clamp cursor
        cursor_y = max(0, min(cursor_y, len(buffer) - 1))
        cursor_x = max(0, min(cursor_x, len(buffer[cursor_y])))

        stdscr.clear()
        draw_status_bar(stdscr, current_filename, buffer, cursor_y, cursor_x)
        for i, line in enumerate(buffer[:height]):
            stdscr.addstr(i, 0, line[:width])
        try:
            stdscr.move(cursor_y, cursor_x)
        except curses.error:
            pass

        stdscr.refresh()

curses.wrapper(main)
