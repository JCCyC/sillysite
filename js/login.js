#!/usr/bin/env node
'use strict';

var path = require('path');
var SillySite = require('./sillysite');
var readPassword = require('./readpass').readPassword;

function main() {
  var baseUrl = process.argv[2];
  var username = process.argv[3];

  if (!baseUrl || !username) {
    console.error('Usage: ' + path.basename(process.argv[1]) + ' <baseurl> <username>');
    process.exit(1);
  }

  readPassword('Password: ')
    .then(function (password) {
      return SillySite.login(baseUrl, username, password);
    })
    .then(function (token) {
      console.log(token);
    })
    .catch(function (err) {
      console.error('Login failed: ' + err.message);
      process.exit(1);
    });
}

main();
