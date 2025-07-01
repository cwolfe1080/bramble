import curses
import textwrap

def main(stdscr):
    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    buffer = ['']
    cursor_y, cursor_x = 0, 0

    while True:
        key = stdscr.getch()

        if key == 27:  # ESC to exit
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

        elif 32 <= key <= 126:
            line = buffer[cursor_y]
            buffer[cursor_y] = line[:cursor_x] + chr(key) + line[cursor_x:]
            cursor_x += 1

            # If the line exceeds width, wrap it intelligently
            if len(buffer[cursor_y]) > width:
                long_line = buffer.pop(cursor_y)
                wrapped = textwrap.wrap(long_line, width)
                buffer[cursor_y:cursor_y] = wrapped
                cursor_y += len(wrapped) - 1
                cursor_x = len(wrapped[-1])

        # Keep cursor within bounds
        if cursor_y >= len(buffer):
            cursor_y = len(buffer) - 1
        if cursor_x > len(buffer[cursor_y]):
            cursor_x = len(buffer[cursor_y])

        # Draw the buffer
        stdscr.clear()
        for i, line in enumerate(buffer[:height]):
            stdscr.addstr(i, 0, line[:width])
        try:
            stdscr.move(cursor_y, cursor_x)
        except curses.error:
            pass
        stdscr.refresh()

curses.wrapper(main)
