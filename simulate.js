const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function getArg(name) {
    const index = process.argv.indexOf(name);
    if (index === -1 || !process.argv[index + 1]) {
        throw new Error(`Нужен аргумент ${name}`);
    }
    return process.argv[index + 1];
}

function run(command, args) {
    const result = spawnSync(command, args, { stdio: 'inherit', shell: true });
    if (result.status !== 0) {
        process.exit(result.status ?? 1);
    }
}

const target = getArg('--target');
const workDir = path.join(__dirname, '.simulate');
const projectJson = path.join(workDir, 'project.json');
const orderResponse = path.join(workDir, 'order-response.json');
const filesDir = path.join(workDir, 'files');

fs.mkdirSync(workDir, { recursive: true });

run('python', ['info2.py', '--target', target, '--output', projectJson, '--output-dir', filesDir]);
run('python', ['ai.py', '--input', projectJson, '--output', orderResponse]);

const indexArgs = ['index.js', '--target-order', target, '--order-response', orderResponse];
if (process.argv.includes('--refresh')) {
    indexArgs.push('--refresh');
}
run('node', indexArgs);
