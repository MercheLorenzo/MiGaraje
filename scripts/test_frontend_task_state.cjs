/* Regression check: front-end and backend use the same overdue/upcoming precedence.
 * Extracts the actual taskState function from the SPA without running the DOM.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const code = fs.readFileSync(path.join(__dirname, '../frontend/js/app.js'), 'utf8');
const match = code.match(/  const taskState = t => \{[\s\S]*?\n  \};/);
assert.ok(match, 'Cannot find taskState in app.js');
const next = (days) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const state = { vehicles: [{ id: 1, current_mileage: 10001 }] };
const run = vm.runInNewContext(`
  const state = ${JSON.stringify(state)};
  const localDate = () => '${next(0)}';
  ${match[0]}
  taskState;
`, { Date });
assert.equal(run({ vehicle_id: 1, due_date: next(5), due_mileage: 10000, status: 'pending' }), 'overdue');
assert.equal(run({ vehicle_id: 1, due_date: next(-1), due_mileage: 90000, status: 'pending' }), 'overdue');
assert.equal(run({ vehicle_id: 1, due_date: next(5), due_mileage: 10000, status: 'completed' }), 'completed');
assert.equal(run({ vehicle_id: 1, due_date: next(40), due_mileage: 10001, status: 'pending' }), 'upcoming');
assert.equal(run({ vehicle_id: 1, due_date: next(60), due_mileage: 20000, status: 'pending' }), 'pending');
console.log('Frontend task state precedence: OK');
