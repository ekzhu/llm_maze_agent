import argparse
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from pyamaze import maze, agent


class MazeGame:
    def __init__(self, maze: maze, agent: agent) -> None:
        self._maze = maze
        self._agent = agent
        self._path = []

    def _look(self):
        x, y = self._agent.position
        possible_next_positions = []
        if self._maze.maze_map[self._agent.position]["E"]:
            possible_next_positions.append((x, y + 1))
        if self._maze.maze_map[self._agent.position]["W"]:
            possible_next_positions.append((x, y - 1))
        if self._maze.maze_map[self._agent.position]["N"]:
            possible_next_positions.append((x - 1, y))
        if self._maze.maze_map[self._agent.position]["S"]:
            possible_next_positions.append((x + 1, y))
        return possible_next_positions

    def look(self, p: str) -> str:
        return "Next possible positions: " + ", ".join([str(p) for p in self._look()])

    def move(self, next_pos: str) -> str:
        x, y = [
            int(p.strip()) for p in next_pos.strip().lstrip("(").rstrip(")").split(",")
        ]
        if (x, y) not in self._look():
            return f"Move failed. Possible next positions are {self.look('')}."
        self._agent.position = (x, y)
        self._path.append((x, y))
        self._maze._win.update()
        if self._agent.position == self._maze._goal:
            return f"Success! You have arrived at the goal at position {self._maze._goal}. Your path taken is {', '.join(str(p) for p in self._path)}."
        return f"Moved to position {self._agent.position}."


parser = argparse.ArgumentParser()
parser.add_argument("--rows", type=int, default=4)
parser.add_argument("--columns", type=int, default=4)
args = parser.parse_args()

m = maze(args.rows, args.columns)
m.CreateMaze()
a = agent(m, shape="arrow", footprints=True)
m._canvas.update()
game = MazeGame(m, a)


tools = [
    Tool(
        name="look",
        func=game.look,
        description="A tool for checking the available next positions to move to. It takes an empty string as input and returns a list of possible next positions.",
    ),
    Tool(
        name="move",
        func=game.move,
        description="A tool for moving in the maze. It takes an input of a target position (x, y), and returns the result of the move. If the move was successful, it returns the new position, otherwise it returns an error. Always use the look tool to check possible directions before making a move.",
    ),
]

llm = ChatOpenAI(temperature=0.0, model="gpt-4")
# llm = ChatOpenAI(temperature=0.0)

agent_chain = initialize_agent(
    tools=tools,
    llm=llm,
    verbose=True,
    max_iterations=100,
)

command = "You are an agent in a rectangular maze with {rows} rows and {columns} columns. Each cell has a position (x, y) where x is the row index and y is the column index. You can move one cell at a time. There may be walls between some cells that you cannot move across. You must move toward the goal using as few steps as possible. You must think about which direction to move using A* search. Your start position is {start}. DO NOT STOP until you have successfully reached the goal position at {goal}.".format(
    rows=m.rows, columns=m.cols, goal=m._goal, start=a.position
)
# print(command)

input("Press any key to start the game.")
agent_chain.run(command)

m.tracePath({a: game._path})
m.run()
