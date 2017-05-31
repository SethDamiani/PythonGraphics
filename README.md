# PythonGraphics

The library is designed to make it very easy for novice programmers to experiment with computer graphics in an object oriented fashion. It is written by [John Zelle](http://mcsp.wartburg.edu/zelle/python/) for use with the book "Python Programming: An Introduction to Computer Science" (Franklin, Beedle & Associates). 

This version was modified by me to add useful features. A complete list of changes made from the original is below. Some parts of this README and the wiki in this repository are taken from [here](http://mcsp.wartburg.edu/zelle/python/) and added to/edited by me.

## Installation

To install this library, put `graphics.py` where it can be imported by python. It should work on any platform where Tkinter is available. It works with Python 2 and 3.

## Getting Started

Here is a complete program to draw a circle of radius 10 centered in a 100x100 window:
```python
from graphics import *

def main():
	win = GraphWin("My Circle", 100, 100)  # Create a new Graphics Window with a title of "My Circle" and dimensions of 100px by 100px
	c = Circle(Point(50, 50), 10)  # Create a Circle object with a center point at (50, 50) and a radius of 10
	c.draw(win)  # Draw the circle in our window
	win.getMouse()  # Pause program for click in window
	win.close()  # Close the window at the end of the program

main()
```
Extensive documentation is available in the wiki.

## Changes From Original

- Add functionality to easily determine when a GraphicsObject was clicked on
- Add ability to check where mouse cursor is
- Add ability to detect right clicks as well as left clicks

## Goals

- Add ability to rotate GraphicsObjects
- Convert clickedOn function into two methods - `Point.isInside(GraphicsObject)` and `GraphicsObject.containsPoint(Point)`
