# class Solution:
#     def sum(self, lst: list, i: int = 0) -> int:
#         if len(lst) == i:
#             return 0
#
#         return lst[i] + self.sum(lst, i + 1)
#
#
# s = Solution()
#
# print(s.sum(lst=[2, 4, 6]))


# infinity = float("inf")
#
# graph = {
#     "start": {
#         "a": 5,
#         "b": 2,
#     },
#     "a": {
#         "c": 4,
#         "d": 2,
#     },
#     "b": {
#         "a": 8,
#         "d": 7,
#     },
#     "c": {
#         "fin": 3,
#         "d": 6,
#     },
#     "d": {
#         "fin": 1,
#     },
#     "fin": {}
# }
# costs = {
#     "a": 5,
#     "b": 2,
#     "c": infinity,
#     "d": infinity,
#     "fin": infinity,
# }
# parents = {
#     "a": "start",
#     "b": "start",
#     "c": None,
#     "d": None,
#     "fin": None,
# }
#
# processed = []
#
# def find_lowest_cost_node(costs):
#     lowest_cost = infinity
#     lowest_cost_node = None
#
#     for node in costs:
#         cost = costs[node]
#         if cost < lowest_cost and node not in processed:
#             lowest_cost = cost
#             lowest_cost_node = node
#     return lowest_cost_node
#
#
# node = find_lowest_cost_node(costs)
# while node is not None:
#     cost = costs[node]
#     neighbors = graph[node]
#     for n in neighbors.keys():
#         new_const = cost + neighbors[n]
#         if costs[n] > new_const:
#             costs[n] = new_const
#             parents[n] = node
#     processed.append(node)
#     node = find_lowest_cost_node(costs)
#
#
# print(graph)
# print(costs)
# print(parents)


def merge(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    """
    Do not return anything, modify nums1 in-place instead.
    """
    nums1[:] = sorted(nums1[:m] + nums2[:n])

nums1 = [1,2,3,0,0,0]
nums2 = [2,5,6]
m = 3
n = 3

merge(nums1, m, nums2, n)

print(nums1)