import { verifyProtocol, initQuickstart } from "./core.js";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log("=".repeat(70));
console.log("DOMAIN ZERO DESKTOP APP - FUNCTION TESTS");
console.log("=".repeat(70));
console.log();

// Test 1: Verify Protocol on Domain Zero Protocol folder
async function testVerifyProtocol() {
  console.log("TEST 1: Verify Protocol");
  console.log("-".repeat(70));

  const testRoot = path.join(__dirname, "..", "..", "Domain Zero Protocol");
  console.log(`Testing against: ${testRoot}`);
  console.log();

  try {
    const result = await verifyProtocol(testRoot);
    console.log(`Result: ${result ? "✅ PASS" : "❌ FAIL"}`);
    console.log();
    return result;
  } catch (error) {
    console.error(`❌ ERROR: ${error.message}`);
    console.log();
    return false;
  }
}

// Test 2: Initialize Quickstart
async function testInitQuickstart() {
  console.log("TEST 2: Initialize Quickstart");
  console.log("-".repeat(70));

  const testRoot = path.join(__dirname, "..", "..", "Domain Zero Protocol");
  console.log(`Testing against: ${testRoot}`);
  console.log();

  try {
    const message = await initQuickstart(testRoot);
    console.log(`Result: ✅ ${message}`);
    console.log();
    return true;
  } catch (error) {
    console.error(`❌ ERROR: ${error.message}`);
    console.log();
    return false;
  }
}

// Test 3: Verify Protocol on invalid folder
async function testVerifyInvalidFolder() {
  console.log("TEST 3: Verify Protocol (Invalid Folder - Should Fail)");
  console.log("-".repeat(70));

  const testRoot = path.join(__dirname, "node_modules");
  console.log(`Testing against: ${testRoot}`);
  console.log();

  try {
    const result = await verifyProtocol(testRoot);
    console.log(`Result: ${result ? "✅ PASS (unexpected)" : "❌ FAIL (expected)"}`);
    console.log();
    return !result; // Should fail, so return true if it failed
  } catch (error) {
    console.log(`Result: ❌ FAIL (expected) - ${error.message}`);
    console.log();
    return true;
  }
}

// Run all tests
async function runTests() {
  console.log("Starting tests...\n");

  const test1 = await testVerifyProtocol();
  const test2 = await testInitQuickstart();
  const test3 = await testVerifyInvalidFolder();

  console.log("=".repeat(70));
  console.log("TEST SUMMARY");
  console.log("=".repeat(70));
  console.log(`Test 1 (Verify Valid Folder):   ${test1 ? "✅ PASS" : "❌ FAIL"}`);
  console.log(`Test 2 (Create Quickstart):     ${test2 ? "✅ PASS" : "❌ FAIL"}`);
  console.log(`Test 3 (Verify Invalid Folder): ${test3 ? "✅ PASS" : "❌ FAIL"}`);
  console.log();

  const allPassed = test1 && test2 && test3;
  console.log(`Overall: ${allPassed ? "✅ ALL TESTS PASSED" : "❌ SOME TESTS FAILED"}`);
  console.log("=".repeat(70));

  process.exit(allPassed ? 0 : 1);
}

runTests();
