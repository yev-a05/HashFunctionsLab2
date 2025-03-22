import hashlib
import random
import struct


def blake2b_16bit(data: bytes) -> int:
    """Обчислення усіченого BLAKE2b (16 біт), з відкиданням старших бітів."""
    hash_full = hashlib.blake2b(data, digest_size=16).digest()  # Генеруємо повний 16-байтовий геш
    return int.from_bytes(hash_full[-2:], 'big')  # Беремо останні 2 байти (молодші 16 біт)


def redundancy_function(x: int, r: bytes) -> bytes:
    """Функція надлишковості R(x) = r || x."""
    return r + struct.pack('H', x)  # r - фіксований випадковий 112-бітний вектор


def generate_precomputation_table(K: int, L: int, r: bytes, redundancy_func) -> dict:
    """Генерує таблицю передобчислень для конкретної функції надлишковості."""
    table = {}
    for _ in range(K):
        x0 = random.randint(0, 2 ** 16 - 1)
        x = x0
        for _ in range(L):
            x = blake2b_16bit(redundancy_func(x, r))
        table[x] = x0
    return table


def find_preimage(tables, L, r, h_value):
    """Пошук прообразу для h за допомогою кількох таблиць передобчислень."""
    y = h_value
    attempts = 0
    for _ in range(L):
        for table in tables:
            if y in table:
                x = table[y]
                for _ in range(L):
                    attempts += 1
                    if blake2b_16bit(redundancy_function(x, r)) == h_value:
                        return x, attempts  # Знайдено прообраз
                    x = blake2b_16bit(redundancy_function(x, r))
        y = blake2b_16bit(redundancy_function(y, r))
    return None, attempts  # Прообраз не знайдено


def experiment(K, L, N):
    """Виконання експерименту для заданих параметрів K, L, N."""
    r = random.randbytes(14)  # Генеруємо випадковий 112-бітний вектор
    print(f"\nЗапуск експерименту для K={K}, L={L}")
    print(f"Згенерований випадковий вектор r: {r.hex()}")

    # Генеруємо K таблиць передобчислень для різних функцій надлишковості
    tables = []
    redundancy_funcs = [redundancy_function]
    for _ in range(K):  # Створюємо K таблиць
        table = generate_precomputation_table(K, L, r, redundancy_funcs[0])
        tables.append(table)

    success_count = 0
    total_attempts = 0
    for _ in range(N):
        x_rand = random.randbytes(32)  # Генеруємо випадкове 256-бітове повідомлення
        h_value = blake2b_16bit(x_rand)  # Обчислюємо його геш
        found_x, attempts = find_preimage(tables, L, r, h_value)
        total_attempts += attempts
        if found_x is not None:
            success_count += 1
            print(f"\nПараметри атаки: K={K}, L={L}")
            print(f"Вхідне 256-бітове повідомлення: {x_rand.hex()}")
            print(f"Геш-значення: {h_value}")
            print(f"Знайдений прообраз: {found_x}")
            print(f"Кількість спроб: {attempts}")

    success_rate = success_count / N * 100
    error_rate = 100 - success_rate
    avg_attempts = total_attempts / N
    print(
        f"K={K}, L={L} -> Успішних знаходжень: {success_rate:.2f}%, Помилок: {error_rate:.2f}%, Середня кількість спроб: {avg_attempts:.2f}")
    return success_rate, error_rate


# Запуск експериментів
N = 10000
for K in [2 ** 10, 2 ** 12, 2 ** 14]:
    for L in [2 ** 5, 2 ** 6, 2 ** 7]:
        experiment(K, L, N)