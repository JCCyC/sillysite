#!/usr/bin/env node
'use strict';

var path = require('path');
var SillySite = require('./sillysite');

function main() {
  var baseUrl = process.argv[2];
  var apiKey = process.argv[3];

  if (!baseUrl || !apiKey) {
    console.error('Usage: ' + path.basename(process.argv[1]) + ' <baseurl> <apikey>');
    process.exit(1);
  }

  SillySite.logout(baseUrl, apiKey)
    .then(function (msg) {
      console.log(msg || 'Logged out');
    })
    .catch(function (err) {
      console.error('Logout failed: ' + err.message);
      process.exit(1);
    });
}

main();
