const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(function (file) {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) {
      if (!file.includes('node_modules') && !file.includes('.next') && !file.includes('.git')) {
        results = results.concat(walk(file));
      }
    } else {
      const ext = path.extname(file);
      if (['.tsx', '.ts', '.css', '.md', '.json', '.html', '.js', '.mjs', '.cjs'].includes(ext)) {
        results.push(file);
      }
    }
  });
  return results;
}

const files = walk('C:/Users/akash/Desktop/capstone MGT 599/frontend');
let changedCount = 0;

files.forEach(f => {
  try {
    let content = fs.readFileSync(f, 'utf8');
    if (content.includes('-') || content.includes('-')) {
      // Replace em-dash (-) and en-dash (-) with normal hyphen (-)
      const newContent = content.replace(/-/g, '-').replace(/-/g, '-');
      fs.writeFileSync(f, newContent);
      changedCount++;
      console.log('Nuked dashes in ' + f);
    }
  } catch (e) {
    console.log('Skipped ' + f);
  }
});

console.log('Total files completely cleared of all AI dashes: ' + changedCount);
