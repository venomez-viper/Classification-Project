const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(function (file) {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory() && !file.includes('node_modules') && !file.includes('.next')) {
      results = results.concat(walk(file));
    } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
      results.push(file);
    }
  });
  return results;
}

const files = walk('C:/Users/akash/Desktop/capstone MGT 599/frontend');
let changed = 0;

files.forEach(f => {
  let content = fs.readFileSync(f, 'utf8');
  if (content.includes('-')) {
    fs.writeFileSync(f, content.replace(/-/g, '-'));
    changed++;
    console.log('Replaced in ' + f);
  }
});

console.log('Total files changed: ' + changed);
