'use strict';

var readline = require('readline');

/**
 * Prompts for one or more passwords in sequence on stdin, masking
 * input when stdin is a real terminal. Resolves to an array of answers
 * in the same order as promptTexts.
 *
 * Uses a single readline interface with a persistent 'line' listener
 * and an internal queue, rather than readline's question() (which only
 * captures the next line per call): piped input can arrive as one
 * burst, with every line already buffered before the first prompt's
 * listener attaches, and lines that arrive with no listener waiting
 * are emitted and lost rather than held for later.
 */
function readPasswords(promptTexts) {
  return new Promise(function (resolve, reject) {
    var isTTY = process.stdin.isTTY === true;
    var rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: isTTY,
    });

    if (isTTY) {
      // The prompt itself is written separately (below); suppress
      // readline's per-keystroke echo/redraw so typed characters
      // never appear on screen.
      rl._writeToOutput = function () {};
    }

    var queue = [];
    var waitingResolve = null;
    var ended = false;

    rl.on('line', function (line) {
      if (isTTY) rl.history = rl.history.slice(1);
      if (waitingResolve) {
        var fn = waitingResolve;
        waitingResolve = null;
        fn(line);
      } else {
        queue.push(line);
      }
    });

    rl.on('close', function () {
      ended = true;
      if (waitingResolve) {
        var fn = waitingResolve;
        waitingResolve = null;
        fn(null);
      }
    });

    function nextLine() {
      if (queue.length > 0) return Promise.resolve(queue.shift());
      if (ended) return Promise.resolve(null);
      return new Promise(function (res) { waitingResolve = res; });
    }

    var answers = [];

    function askNext(index) {
      if (index >= promptTexts.length) {
        rl.close();
        resolve(answers);
        return;
      }
      rl.output.write(promptTexts[index]);
      nextLine().then(function (line) {
        process.stdout.write('\n');
        if (line === null) {
          rl.close();
          reject(new Error('Unexpected end of input'));
          return;
        }
        answers.push(line);
        askNext(index + 1);
      });
    }

    askNext(0);
  });
}

/**
 * Prompts on stdout and reads one line from stdin without echoing it
 * back (when stdin is a TTY). Resolves to the entered text.
 */
function readPassword(promptText) {
  return readPasswords([promptText]).then(function (answers) { return answers[0]; });
}

module.exports = { readPassword: readPassword, readPasswords: readPasswords };
