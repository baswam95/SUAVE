Merge "cruise.stl";
Physical Surface("VEHICLE") = {1, 2, 3, 4};
Physical Surface("SYMPLANE") = {5};
Physical Surface("FARFIELD") = {6};
Surface Loop(7) = {6};
Surface Loop(8) = {5};
Surface Loop(9) = {1};
Surface Loop(10) = {2};
Surface Loop(11) = {3};
Surface Loop(12) = {4};
Volume(12) = {7, 8, 9, 10, 11, 12};
