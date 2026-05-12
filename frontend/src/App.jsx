import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import CountSheet from './pages/CountSheet'

const Placeholder = ({ title }) => <div className="p-4 pb-20 text-white">{title}</div>

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/count" element={<CountSheet />} />
        <Route path="/variance" element={<Placeholder title="Variance Report" />} />
        <Route path="/pos-import" element={<Placeholder title="POS Import" />} />
        <Route path="/products" element={<Placeholder title="Products" />} />
        <Route path="/purchases" element={<Placeholder title="Purchases" />} />
      </Routes>
    </Layout>
  )
}
