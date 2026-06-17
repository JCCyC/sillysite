#!/usr/bin/env node
'use strict';

var path = require('path');
var SillySite = require('./sillysite');
var readPasswords = require('./readpass').readPasswords;

function main() {
  var baseUrl = process.argv[2];
  var username = process.argv[3];

  if (!baseUrl || !username) {
    console.error('Usage: ' + path.basename(process.argv[1]) + ' <baseurl> <username>');
    process.exit(1);
  }

  readPasswords(['Current password: ', 'New password: ', 'Confirm new password: '])
    .then(function (answers) {
      var oldPassword = answers[0], newPassword = answers[1], confirmPassword = answers[2];
      if (newPassword !== confirmPassword) {
        console.error('Change password failed: passwords do not match');
        process.exit(1);
      }
      return SillySite.changepw(baseUrl, username, oldPassword, newPassword);
    })
    .then(function () {
      console.log('Password changed successfully');
    })
    .catch(function (err) {
      console.error('Change password failed: ' + err.message);
      process.exit(1);
    });
}

main();
