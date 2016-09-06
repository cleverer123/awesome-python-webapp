#include <iostream>
#include <cstdio>
#include <algorithm>
using namespace std;

const int MAXM = 100000 + 10;

typedef pair<int,int> PII;

int N, M;
PII data[MAXM];

inline int ABS(int x)
{
    if (x >= 0) return x; else return -x;
}

int main()
{
    while (cin >> N >> M)
    {
        int ans = 0;
        for (int i = 1; i <= M; ++i)
        {
            int a, b;
            scanf("%d%d", &a, &b);
            data[i] = make_pair(a, b);
        }

        sort(data + 1, data + M + 1);

        bool flag = 1;

        for (int i = 2; i <= M; ++i)
            if (data[i].first - data[i - 1].first < ABS(data[i].second - data[i - 1].second))
            {
                flag = 0;
                break;
            }

        if (!flag)
            puts("IMPOSSIBLE");
        else
        {

            if (data[1].first != 1)
                ans = max(ans, data[1].second + data[1].first - 1);
            else
                ans = max(ans, data[1].second);

            if (data[M].first != N)
                ans = max(ans, data[M].second + N - data[M].first);
            else
                ans = max(ans, data[M].second);

            for (int i = 2; i <= M; ++i)
            {
                ans = max(ans, ((data[i].first - data[i - 1].first) -  ABS(data[i].second - data[i - 1].second)) / 2 );
                ans = max(ans, data[i].second);
            }

            printf("%d\n", ans);
        }
    }
    return 0;
}