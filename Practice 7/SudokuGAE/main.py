from flask import Flask, render_template, request

app = Flask(__name__)

# A sample solved Sudoku board
SOLVED_BOARD = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9]
]

# The board displayed to the player (some cells are hidden)
PUZZLE_BOARD = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
]

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    board = PUZZLE_BOARD
    
    if request.method == 'POST':
        # Get user input data
        user_input = []
        try:
            correct = True
            for r in range(9):
                row_data = []
                for c in range(9):
                    val = request.form.get(f'cell-{r}-{c}')
                    val = int(val) if val else 0
                    row_data.append(val)
                    if val != SOLVED_BOARD[r][c]:
                        correct = False
                user_input.append(row_data)
            
            if correct:
                message = "Congratulations! You solved it!"
            else:
                message = "Incorrect solution. Try again!"
            board = user_input # Re-display what the user just entered
        except ValueError:
            message = "Invalid input! Please enter numbers only."

    return render_template('index.html', board=board, message=message)

if __name__ == '__main__':
    # Run locally for testing
    app.run(host='127.0.0.1', port=8080, debug=True)
