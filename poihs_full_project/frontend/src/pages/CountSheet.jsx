import axios from 'axios'
import clsx from 'clsx'
import { CheckCircle2, ChevronDown, ChevronRight, Minus, Plus, Save, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { useQuery } from 'react-query'

const venueId = '00000000-0000-0000-0000-000000000001'
const sessionId = '00000000-0000-0000-0000-000000000001'

function getBottleLabel(product) {
  if (product.type === 'Draft') return 'Draft'
  if (product.bottle_size_ml) return `${product.bottle_size_ml}ml`
  return product.type
}

export default function CountSheet() {
  const [search, setSearch] = useState('')
  const [collapsed, setCollapsed] = useState({})
  const [counts, setCounts] = useState({})

  const { data: products = [], isLoading } = useQuery(['products', venueId], async () => {
    const response = await axios.get(`/api/v1/products?venue_id=${venueId}`)
    return response.data
  })

  const grouped = useMemo(() => {
    const filtered = products.filter((product) =>
      product.name.toLowerCase().includes(search.toLowerCase()),
    )
    const map = {}
    for (const product of filtered) {
      const category = product.category?.name || 'Uncategorized'
      if (!map[category]) map[category] = []
      map[category].push(product)
    }
    Object.keys(map).forEach((key) => {
      map[key].sort((a, b) => a.name.localeCompare(b.name))
    })
    return map
  }, [products, search])

  const updateValue = (productId, field, amount) => {
    setCounts((prev) => {
      const current = prev[productId] || {
        count_750ml: 0,
        count_1L: 0,
        count_1_75L: 0,
        count_draft_tenths: 0,
        notes: '',
      }
      return {
        ...prev,
        [productId]: {
          ...current,
          [field]: Math.max(0, Number((current[field] || 0) + amount).toFixed(2)),
        },
      }
    })
  }

  const setManualValue = (productId, field, value) => {
    setCounts((prev) => ({
      ...prev,
      [productId]: {
        ...(prev[productId] || {}),
        [field]: Number(value || 0),
      },
    }))
  }

  const setNotes = (productId, value) => {
    setCounts((prev) => ({
      ...prev,
      [productId]: {
        ...(prev[productId] || {}),
        notes: value,
      },
    }))
  }

  const totalProducts = products.length
  const countedProducts = Object.values(counts).filter((item) =>
    (item.count_750ml || 0) + (item.count_1L || 0) + (item.count_1_75L || 0) + (item.count_draft_tenths || 0) > 0,
  ).length

  const calculateTotalMl = (product, count) => {
    if (!count) return 0
    return (
      (Number(count.count_750ml || 0) * 750) +
      (Number(count.count_1L || 0) * 1000) +
      (Number(count.count_1_75L || 0) * 1750) +
      (Number(count.count_draft_tenths || 0) * Number(product.keg_size_ml || 0) / 10)
    )
  }

  const handleSave = async () => {
    try {
      const payload = Object.entries(counts).map(([product_id, value]) => ({ product_id, ...value }))
      await axios.post(`/api/v1/inventory/sessions/${sessionId}/counts/bulk`, payload)
      toast.success('Counts saved successfully')
    } catch (error) {
      toast.error('Failed to save counts')
    }
  }

  if (isLoading) return <div className="p-4 pb-28">Loading count sheet...</div>

  return (
    <div className="pb-32">
      <div className="sticky top-0 z-20 border-b border-gray-700 bg-gray-900 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search products"
            className="input-field pl-10"
          />
        </div>
        <p className="mt-3 text-sm text-gray-400">{countedProducts} of {totalProducts} products counted</p>
      </div>

      <div className="space-y-4 p-4">
        {Object.entries(grouped).map(([category, categoryProducts]) => {
          const isCollapsed = collapsed[category]
          return (
            <section key={category} className="card p-0 overflow-hidden">
              <button
                className="flex w-full items-center justify-between px-4 py-4 text-left"
                onClick={() => setCollapsed((prev) => ({ ...prev, [category]: !prev[category] }))}
              >
                <span className="text-lg font-semibold">{category}</span>
                {isCollapsed ? <ChevronRight size={18} /> : <ChevronDown size={18} />}
              </button>

              {!isCollapsed && (
                <div className="space-y-3 border-t border-gray-700 p-4">
                  {categoryProducts.map((product) => {
                    const count = counts[product.id] || {}
                    const totalMl = calculateTotalMl(product, count)
                    const isCounted = totalMl > 0
                    const isDraft = product.type === 'Draft'

                    return (
                      <div key={product.id} className="rounded-xl border border-gray-700 bg-gray-850 p-4">
                        <div className="mb-3 flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium">{product.name} - {getBottleLabel(product)}</p>
                            <p className="text-sm text-gray-400">Total ML: {totalMl.toFixed(0)}</p>
                          </div>
                          {isCounted && <CheckCircle2 className="text-green-400" size={20} />}
                        </div>

                        {isDraft ? (
                          <div className="space-y-2">
                            <p className="text-sm text-gray-300">Draft (tenths)</p>
                            <div className="flex items-center gap-3">
                              <button className="count-button min-h-[48px] min-w-[48px]" onClick={() => updateValue(product.id, 'count_draft_tenths', -0.1)}><Minus size={18} /></button>
                              <input
                                type="number"
                                step="0.1"
                                value={count.count_draft_tenths || 0}
                                onChange={(e) => setManualValue(product.id, 'count_draft_tenths', e.target.value)}
                                className="input-field text-center"
                              />
                              <button className="count-button min-h-[48px] min-w-[48px]" onClick={() => updateValue(product.id, 'count_draft_tenths', 0.1)}><Plus size={18} /></button>
                            </div>
                          </div>
                        ) : (
                          <div className="grid gap-3">
                            {[
                              ['count_750ml', '0.75L', 0.25],
                              ['count_1L', '1L', 0.25],
                              ['count_1_75L', '1.75L', 0.25],
                            ].map(([field, label, step]) => (
                              <div key={field}>
                                <p className="mb-2 text-sm text-gray-300">{label}</p>
                                <div className="flex items-center gap-3">
                                  <button className="count-button min-h-[48px] min-w-[48px]" onClick={() => updateValue(product.id, field, -step)}><Minus size={18} /></button>
                                  <input
                                    type="number"
                                    step={step}
                                    value={count[field] || 0}
                                    onChange={(e) => setManualValue(product.id, field, e.target.value)}
                                    className="input-field text-center"
                                  />
                                  <button className="count-button min-h-[48px] min-w-[48px]" onClick={() => updateValue(product.id, field, step)}><Plus size={18} /></button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        <textarea
                          placeholder="Notes"
                          value={count.notes || ''}
                          onChange={(e) => setNotes(product.id, e.target.value)}
                          className="input-field mt-3 min-h-[72px]"
                        />
                      </div>
                    )
                  })}
                </div>
              )}
            </section>
          )
        })}
      </div>

      <div className="fixed bottom-20 left-0 right-0 px-4">
        <button onClick={handleSave} className={clsx('btn-primary flex w-full items-center justify-center gap-2 shadow-lg')}>
          <Save size={18} />
          Save Counts
        </button>
      </div>
    </div>
  )
}
