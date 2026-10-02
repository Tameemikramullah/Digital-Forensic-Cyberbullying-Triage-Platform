export default function IntegrityVerification() {
  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl font-bold mb-4">Integrity Verification</h2>
      <p className="text-sm text-gray-600 mb-4">
        Verify that the evidence content has not been altered since upload by recalculating the SHA-256 hash.
      </p>
      <div className="flex items-center gap-4">
        <button className="bg-gray-600 text-white px-4 py-2 rounded">
          Verify Integrity
        </button>
        <span className="text-sm text-gray-500">Status: Pending</span>
      </div>
    </div>
  )
}
