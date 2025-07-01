import curses
import textwrap

def save_to_file(buffer, filename="document.txt"):
    with open(filename, "w") as f:
        for line in buffer:
            f.write(line + "\n")

def load_from_file(filename="document.txt"):
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

def main(stdscr):
    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    buffer = ['']
    cursor_y, cursor_x = 0, 0

    while True:
        key = stdscr.getch()

        if key == 17:  # ESC to exit
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

        elif key == 23:  # Ctrl+W to save
            save_to_file(buffer)

        elif key == 15:  # Ctrl+O to load
            buffer = load_from_file()
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
        for i, line in enumerate(buffer[:height]):
            stdscr.addstr(i, 0, line[:width])
        try:
            stdscr.move(cursor_y, cursor_x)
        except curses.error:
            pass
        stdscr.refresh()

curses.wrapper(main)
