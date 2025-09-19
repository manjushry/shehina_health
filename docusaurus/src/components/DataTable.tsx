import React, {useMemo, useState} from 'react';

export type Column<T> = {
  key: keyof T & string;
  header: string;
  width?: string | number;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
};

export type DataTableProps<T extends Record<string, any>> = {
  columns: Column<T>[];
  data: T[];
  searchable?: boolean;
  pageSize?: number;
};

export default function DataTable<T extends Record<string, any>>({
  columns,
  data,
  searchable = true,
  pageSize = 10,
}: DataTableProps<T>) {
  const [q, setQ] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    if (!q) return data;
    const needle = q.toLowerCase();
    return data.filter((row) =>
      Object.values(row).some((v) =>
        String((v as any)?.props?.children ?? v).toLowerCase().includes(needle)
      )
    );
  }, [data, q]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    const arr = [...filtered];
    arr.sort((a, b) => {
      const av = (a as any)[sortKey];
      const bv = (b as any)[sortKey];
      const aStr = String(av?.props?.children ?? av).toLowerCase();
      const bStr = String(bv?.props?.children ?? bv).toLowerCase();
      if (aStr < bStr) return sortDir === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const pageData = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, page, pageSize]);

  const setSort = (key: string, enabled: boolean) => {
    if (!enabled) return;
    if (sortKey !== key) {
      setSortKey(key);
      setSortDir('asc');
    } else {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    }
  };

  return (
    <div>
      {searchable && (
        <div style={{marginBottom: 8}}>
          <input
            type="text"
            placeholder="Buscar..."
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
            style={{width: '100%', maxWidth: 420}}
          />
        </div>
      )}

      <div style={{overflowX: 'auto'}}>
        <table className="table">
          <thead>
            <tr>
              {columns.map((c) => (
                <th
                  key={c.key}
                  style={{cursor: c.sortable ? 'pointer' : 'default', width: c.width}}
                  onClick={() => setSort(c.key, !!c.sortable)}
                  title={c.sortable ? 'Ordenar' : undefined}
                >
                  {c.header}
                  {sortKey === c.key && (
                    <span style={{marginLeft: 6}}>{sortDir === 'asc' ? '▲' : '▼'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageData.map((row, idx) => (
              <tr key={idx}>
                {columns.map((c) => (
                  <td key={c.key}>
                    {c.render ? c.render(row) : (row as any)[c.key]}
                  </td>
                ))}
              </tr>
            ))}
            {pageData.length === 0 && (
              <tr>
                <td colSpan={columns.length} style={{textAlign: 'center', padding: 16}}>
                  Sin resultados
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
        <button className="button button--secondary" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
          Anterior
        </button>
        <span>
          Página {page} de {totalPages}
        </span>
        <button className="button button--secondary" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
          Siguiente
        </button>
      </div>
    </div>
  );
}
