import curses

def main(stdscr):
    curses.curs_set(1)
    stdscr.clear()

    # Get the size of the terminal
    height, width = stdscr.getmaxyx()

    buffer = ['']
    cursor_y, cursor_x = 0, 0

    while True:
        key = stdscr.getch()

        # Exit program on ESC
        if key == 27:
            break

        # ENTER key → new line
        elif key in (10, 13):
            buffer.insert(cursor_y + 1, '')
            cursor_y += 1
            cursor_x = 0

        # Backspace handling
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if cursor_x > 0:
                line = buffer[cursor_y]
                buffer[cursor_y] = line[:cursor_x - 1] + line[cursor_x:]
                cursor_x -= 1
            elif cursor_y > 0:
                prev_line = buffer.pop(cursor_y)
                cursor_y -= 1
                cursor_x = len(buffer[cursor_y])
                buffer[cursor_y] += prev_line

        # Printable character input
        elif 32 <= key <= 126:
            line = buffer[cursor_y]
            buffer[cursor_y] = line[:cursor_x] + chr(key) + line[cursor_x:]
            cursor_x += 1

            # Wrap line if too long
            if cursor_x >= width:
                buffer.insert(cursor_y + 1, buffer[cursor_y][width:])
                buffer[cursor_y] = buffer[cursor_y][:width]
                cursor_y += 1
                cursor_x = len(buffer[cursor_y])

        # Prevent overflow
        if cursor_y >= height:
            cursor_y = height - 1
        if cursor_x >= width:
            cursor_x = width - 1

        # Draw buffer
        stdscr.clear()
        for i, line in enumerate(buffer[:height]):
            stdscr.addstr(i, 0, line[:width])
        try:
            stdscr.move(cursor_y, cursor_x)
        except curses.error:
            pass  # Quietly skip errors if cursor is off-screen
        stdscr.refresh()

curses.wrapper(main)
